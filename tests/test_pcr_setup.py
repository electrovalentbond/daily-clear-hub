import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import yaml

from core.config_loader import GameConfig
from core.pcr_backend import check_pcr, run_pcr
from core.pcr_setup import PCR_PACKAGE, discover_pcr


class TestPcrDiscovery(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.tools = Path(self.directory.name)
        self.game = GameConfig("公主连结", False, "native", 300, {})

    def install_fixture(self):
        project = self.tools / "pcr-script"
        for relative in (
            ".venv/Scripts/python.exe",
            "daily_task.py",
            "images/btn_ok.png",
            "pcrscript/runtime.py",
        ):
            path = project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        adb = self.tools / "platform-tools" / "adb.exe"
        adb.parent.mkdir()
        adb.touch()
        return project, adb.resolve()

    @patch("core.pcr_setup._adb_output")
    def test_absent_install_and_hand_config_never_probe_adb(self, adb_output):
        self.assertIsNone(discover_pcr(self.game, self.tools))
        manual = GameConfig("公主连结", True, "pcr_script", 600, {"pcr_config": "custom.yml"})
        self.assertIs(discover_pcr(manual, self.tools), manual)
        adb_output.assert_not_called()

    @patch("core.pcr_setup._adb_output")
    def test_checks_only_authorized_devices_for_exact_package(self, adb_output):
        project, adb = self.install_fixture()
        adb_output.side_effect = (
            "List of devices attached\n"
            "device-a\tdevice\ndevice-offline\toffline\n"
            "device-b\tdevice\ndevice-locked\tunauthorized\n",
            "",
            "package:/data/app/com.bilibili.priconne/base.apk\n",
        )
        resolved = discover_pcr(self.game, self.tools)
        self.assertIsNotNone(resolved)
        self.assertEqual("pcr_script", resolved.backend)
        self.assertEqual(1800, resolved.timeout)
        self.assertEqual(project.resolve(), resolved.path("project_dir"))
        self.assertEqual([call.args for call in adb_output.call_args_list], [
            (adb, "devices"),
            (adb, "-s", "device-a", "shell", "pm", "path", PCR_PACKAGE),
            (adb, "-s", "device-b", "shell", "pm", "path", PCR_PACKAGE),
        ])
        check_pcr(resolved)

        def record_process(command, cwd, timeout, *, stdout):
            config = Path(command[-1])
            self.assertEqual(resolved.path("project_dir"), cwd)
            values = yaml.safe_load(config.read_text(encoding="utf-8"))
            self.assertEqual("device-b", values["Extra"]["adb_serial"])
            self.assertFalse(values["Gift"]["auto_dismantle"])
            self.assertEqual([["schedule"], ["get_quest_reward"], ["get_gift", True]], values["Task"][1])
            stdout.write(json.dumps({
                "status": "complete", "verified": True,
                "tasks": [{"task": "schedule", "status": "already_complete"}],
            }).encode())
            self.generated_config = config
            return 0

        run_pcr(resolved, record_process)
        self.assertFalse(self.generated_config.exists())
        self.assertFalse((project / "daily_config.yml").exists())

    @patch("core.pcr_setup._adb_output")
    def test_ambiguous_target_fails_and_named_serial_disambiguates(self, adb_output):
        _, adb = self.install_fixture()
        devices = "first\tdevice\nsecond\tdevice\n"
        package = "package:/data/app/com.bilibili.priconne/base.apk\n"
        adb_output.side_effect = [devices, package, package]
        with self.assertRaisesRegex(ValueError, "多个.*ADB"):
            discover_pcr(self.game, self.tools)
        game = GameConfig("公主连结", False, "native", 1800, {"adb_serial": "second"})
        adb_output.reset_mock()
        adb_output.side_effect = [devices, package]
        self.assertIsNotNone(discover_pcr(game, self.tools))
        self.assertEqual(adb_output.call_count, 2)
        adb_output.assert_called_with(adb, "-s", "second", "shell", "pm", "path", PCR_PACKAGE)
