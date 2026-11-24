import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, patch

from scripts import automas_keep_emulator as keep_emulator


PORT = 36163
SERIAL = "emulator-5554"
EMULATOR_ID = "11111111-1111-4111-8111-111111111111"
SUCCESS = {"code": 200, "status": "success"}


class KeepEmulatorTest(unittest.TestCase):
    def setUp(self):
        root = self.enterContext(tempfile.TemporaryDirectory())
        self.adb = (Path(root) / "LDPlayer" / "adb.exe").resolve()

    @patch.object(keep_emulator, "_adb_output")
    def test_selects_authorized_loopback_only(self, adb_output):
        adb_output.return_value = (
            b"List of devices attached\r\n"
            b"AB12\tdevice\r\n"
            b"192.168.1.5:5555\tdevice\r\n"
            b"emulator-5554\tdevice\r\n"
            b"emulator-5556\toffline\r\n"
        )
        self.assertEqual(keep_emulator._select_serial(self.adb, None), SERIAL)
        with self.assertRaisesRegex(ValueError, "未连接所选"):
            keep_emulator._select_serial(self.adb, "emulator-5556")

    @patch.object(keep_emulator, "_adb_output")
    def test_multiple_devices_require_explicit_serial(self, adb_output):
        adb_output.return_value = b"emulator-5554\tdevice\n127.0.0.1:5557\tdevice\n"
        with self.assertRaisesRegex(ValueError, "多个本地模拟器"):
            keep_emulator._select_serial(self.adb, None)
        self.assertEqual(keep_emulator._select_serial(self.adb, "127.0.0.1:5557"), "127.0.0.1:5557")

    @patch.object(keep_emulator.subprocess, "Popen")
    def test_only_adb_monitor_is_stopped_after_probe(self, popen):
        tracker = popen.return_value.__enter__.return_value
        tracker.wait.side_effect = subprocess.TimeoutExpired("adb track-devices", 1)

        keep_emulator._check_tracker(self.adb)

        self.assertEqual(popen.call_args.args[0], [str(self.adb), "track-devices"])
        tracker.kill.assert_called_once_with()

    @patch.object(keep_emulator, "_check_health")
    @patch.object(keep_emulator, "_snapshot_task_ids", return_value=set())
    @patch.object(keep_emulator, "_request")
    def test_creates_separate_device_and_reuses_it_when_registered(self, request, snapshot, _health):
        native = {"existing": {"Info": {"Name": "模拟器 2.0", "Type": "emulator2"}}}
        info = {
            "Type": "general",
            "Name": keep_emulator._emulator_name(SERIAL),
            "Path": str(self.adb),
            "MaxWaitTime": 5,
        }
        request.side_effect = [
            {**SUCCESS, "data": native},
            {**SUCCESS, "emulatorId": EMULATOR_ID},
            SUCCESS,
            {**SUCCESS, "data": {**native, EMULATOR_ID: {"Info": info}}},
        ]

        keep_emulator._register(PORT, self.adb, SERIAL)
        keep_emulator._register(PORT, self.adb, SERIAL)

        snapshot.assert_called_once_with(PORT)
        self.assertEqual(request.call_args_list, [
            call(PORT, "/api/emulator/get", {}),
            call(PORT, "/api/emulator/add", {}),
            call(PORT, "/api/emulator/update", {"emulatorId": EMULATOR_ID, "data": {"Info": info}}),
            call(PORT, "/api/emulator/get", {}),
        ])

    @patch.object(keep_emulator, "_check_health")
    @patch.object(keep_emulator, "_snapshot_task_ids", return_value=set())
    @patch.object(keep_emulator, "_request")
    def test_failed_save_removes_only_new_device(self, request, _snapshot, _health):
        request.side_effect = [
            {**SUCCESS, "data": {}},
            {**SUCCESS, "emulatorId": EMULATOR_ID},
            {"code": 500, "status": "error", "message": "路径无效"},
            SUCCESS,
        ]

        with self.assertRaisesRegex(ValueError, "路径无效"):
            keep_emulator._register(PORT, self.adb, SERIAL)

        self.assertEqual(request.call_args, call(PORT, "/api/emulator/delete", {"emulatorId": EMULATOR_ID}))
