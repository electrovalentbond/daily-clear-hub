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

    @patch.object(keep_emulator, "_program_output")
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

    @patch.object(keep_emulator, "_program_output")
    def test_multiple_devices_require_explicit_serial(self, adb_output):
        devices = b"emulator-5554\tdevice\n127.0.0.1:5557\tdevice\n"
        adb_output.side_effect = [devices, devices, b"device\n"]
        with self.assertRaisesRegex(ValueError, "多个本地模拟器"):
            keep_emulator._select_serials(self.adb, [])
        serials = ["127.0.0.1:5557", SERIAL]
        self.assertEqual(keep_emulator._select_serials(self.adb, [*serials, SERIAL]), serials)
        self.assertEqual(adb_output.call_args_list, [
            call(self.adb, "devices"), call(self.adb, "devices"), call(self.adb, "-s", serials[0], "get-state"),
        ])

    @patch.object(keep_emulator, "_program_output")
    def test_explicit_loopback_reconnects_only_requested_target(self, adb_output):
        endpoint = "127.0.0.1:5557"
        adb_output.side_effect = [
            b"emulator-5554\tdevice\n",
            b"connected to 127.0.0.1:5557\n",
            b"emulator-5554\tdevice\n127.0.0.1:5557\tdevice\n",
            b"device\n",
        ]

        self.assertEqual(keep_emulator._select_serials(self.adb, [endpoint]), [endpoint])
        self.assertEqual(adb_output.call_args_list, [
            call(self.adb, "devices"), call(self.adb, "connect", endpoint), call(self.adb, "devices"),
            call(self.adb, "-s", endpoint, "get-state"),
        ])

    @patch.object(keep_emulator, "_program_output")
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

    @patch.object(keep_emulator, "_program_output", return_value=b"emulator-5554\tdevice\nemulator-5556\tdevice\n")
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

    @patch.object(keep_emulator, "_program_output")
    @patch.object(keep_emulator, "_check_tracker")
    @patch.object(keep_emulator, "_register")
    def test_ldplayer_index_registers_verified_tcp_even_when_the_serial_is_missing(self, register, tracker, output):
        self.adb.parent.mkdir()
        self.adb.touch()
        console = self.adb.with_name("ldconsole.exe")
        console.touch()
        endpoint = "127.0.0.1:5555"
        output.side_effect = [
            b"0,LDPlayer, BH2,100,200,1,300,400,1280,720,240\r\n",
            b"emulator-5556\tdevice\n",
            b"connected to 127.0.0.1:5555\n",
            b"emulator-5556\tdevice\n127.0.0.1:5555\tdevice\n",
            b"device\n",
        ]
        with patch("sys.argv", ["automas_keep_emulator", "register", "--adb", str(self.adb), "--ld-index", "0"]):
            with redirect_stdout(io.StringIO()) as registered:
                self.assertEqual(keep_emulator.main(), 0)

        self.assertEqual(output.call_args_list, [
            call(console, "list2"), call(self.adb, "devices"), call(self.adb, "connect", endpoint),
            call(self.adb, "devices"), call(self.adb, "-s", endpoint, "get-state"),
        ])
        register.assert_called_once_with(PORT, self.adb, endpoint)
        tracker.assert_called_once_with(self.adb)
        self.assertIn("track-devices | 127.0.0.1:5555", registered.getvalue())

    @patch.object(keep_emulator, "_program_output", return_value=(
        b"0,LDPlayer,100,200,0,-1,-1,1280,720,240\n"
        b"1,LDPlayer-1,100,200,1,300,400,1280,720,240\n"
    ))
    def test_ldplayer_index_requires_the_selected_instance_to_be_running(self, output):
        self.adb.parent.mkdir()
        console = self.adb.with_name("dnconsole.exe")
        console.touch()
        self.assertEqual(keep_emulator._ldplayer_addresses(self.adb, [1, 1]), ["127.0.0.1:5557"])
        with self.assertRaisesRegex(ValueError, "先打开雷电实例 0"):
            keep_emulator._ldplayer_addresses(self.adb, [0, 1])
        with self.assertRaisesRegex(ValueError, "找不到雷电实例 2"):
            keep_emulator._ldplayer_addresses(self.adb, [2])
        self.assertTrue(all(request == call(console, "list2") for request in output.call_args_list))

    @patch.object(keep_emulator, "_program_output")
    def test_loopback_is_rejected_if_the_runner_get_state_probe_fails(self, output):
        endpoint = "127.0.0.1:5555"
        output.side_effect = [b"127.0.0.1:5555\tdevice\n", subprocess.CalledProcessError(
            1, [str(self.adb), "-s", endpoint, "get-state"], stderr=b"device not found",
        )]
        with self.assertRaisesRegex(ValueError, "127.0.0.1:5555 未就绪（device not found）"):
            keep_emulator._select_serials(self.adb, [endpoint])

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
