import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
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
        self.assertEqual(keep_emulator._select_serials(self.adb, []), [SERIAL])
        with self.assertRaisesRegex(ValueError, "emulator-5556（offline）"):
            keep_emulator._select_serials(self.adb, ["emulator-5556"])
        with self.assertRaisesRegex(ValueError, "emulator-5558（未出现在 adb devices 中）"):
            keep_emulator._select_serials(self.adb, ["emulator-5558"])

    @patch.object(keep_emulator, "_adb_output")
    def test_multiple_devices_require_explicit_serial(self, adb_output):
        adb_output.return_value = b"emulator-5554\tdevice\n127.0.0.1:5557\tdevice\n"
        with self.assertRaisesRegex(ValueError, "多个本地模拟器"):
            keep_emulator._select_serials(self.adb, [])
        serials = ["127.0.0.1:5557", SERIAL]
        self.assertEqual(keep_emulator._select_serials(self.adb, [*serials, SERIAL]), serials)
        self.assertTrue(all(c == call(self.adb, "devices") for c in adb_output.call_args_list))

    @patch.object(keep_emulator, "_adb_output")
    def test_explicit_loopback_reconnects_only_requested_target(self, adb_output):
        endpoint = "127.0.0.1:5557"
        adb_output.side_effect = [
            b"emulator-5554\tdevice\n",
            b"connected to 127.0.0.1:5557\n",
            b"emulator-5554\tdevice\n127.0.0.1:5557\tdevice\n",
        ]

        self.assertEqual(keep_emulator._select_serials(self.adb, [endpoint]), [endpoint])
        self.assertEqual(adb_output.call_args_list, [
            call(self.adb, "devices"), call(self.adb, "connect", endpoint), call(self.adb, "devices"),
        ])

    @patch.object(keep_emulator, "_adb_output")
    def test_only_online_loopback_is_accepted_even_when_connect_command_exits_cleanly(self, adb_output):
        endpoint = "127.0.0.1:5557"
        adb_output.side_effect = [b"", b"failed to connect: connection refused", b""]

        with self.assertRaisesRegex(ValueError, "connection refused"):
            keep_emulator._select_serials(self.adb, [endpoint])

        adb_output.reset_mock(side_effect=True)
        adb_output.return_value = b"192.168.1.5:5557\tdevice\n"
        with self.assertRaisesRegex(ValueError, "无效的本地模拟器地址"):
            keep_emulator._select_serials(self.adb, ["192.168.1.5:5557"])
        adb_output.assert_called_once_with(self.adb, "devices")

    @patch.object(keep_emulator, "_adb_output", return_value=b"emulator-5554\tdevice\nemulator-5556\tdevice\n")
    @patch.object(keep_emulator, "_check_tracker")
    @patch.object(keep_emulator, "_register")
    def test_register_can_create_two_separately_named_bindings(self, register, check_tracker, _adb_output):
        self.adb.parent.mkdir()
        self.adb.touch()
        command = ["automas_keep_emulator", "register", "--adb", str(self.adb),
                   "--serial", SERIAL, "--serial", "emulator-5556"]
        with patch("sys.argv", command), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(keep_emulator.main(), 0)

        self.assertEqual(register.call_args_list, [call(PORT, self.adb, SERIAL), call(PORT, self.adb, "emulator-5556")])
        check_tracker.assert_called_once_with(self.adb)
        self.assertIn("track-devices | emulator-5554", output.getvalue())
        self.assertIn("track-devices | emulator-5556", output.getvalue())

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
