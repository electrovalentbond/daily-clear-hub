import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "integrations" / "pcr-automas"


class PcrAutomasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("pcr_automas_agent", PROJECT / "agent.py")
        cls.agent = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {
            "maa.agent.agent_server": SimpleNamespace(
                AgentServer=SimpleNamespace(custom_action=lambda _: lambda action: action)
            ),
            "maa.custom_action": SimpleNamespace(CustomAction=object),
        }):
            spec.loader.exec_module(cls.agent)
        cls.profile = json.loads((PROJECT / "interface.json").read_text(encoding="utf-8"))

    def context(self, adb, choices):
        pipeline = json.loads((PROJECT / "resource/pipeline/daily.json").read_text(encoding="utf-8"))
        for case in self.profile["option"]["DailyActivities"]["cases"]:
            if case["name"] in choices:
                for name, override in case["pipeline_override"].items():
                    pipeline[name].update(override)
        return SimpleNamespace(
            get_node_data=pipeline.get,
            tasker=SimpleNamespace(stopping=False, controller=SimpleNamespace(info={
                "type": "adb", "adb_path": str(adb), "adb_serial": "emulator-5556",
            })),
        )

    def test_gui_selection_uses_bound_device_and_preserves_non_stamina_gift_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            adb = project / "adb.exe"
            adb.touch()
            (project / "daily_task.py").touch()
            context = self.context(adb, {"QuestReward", "Gift"})
            installation = project / "local.json"
            installation.write_text(json.dumps({"hub_root": str(ROOT), "pcr_root": directory}), encoding="utf-8")
            log_path = project / "logs" / "pcr-automas.log"
            with (
                patch.object(self.agent, "INSTALL_CONFIG", installation),
                patch.object(self.agent, "LOG_PATH", log_path),
                patch("core.scheduler.run_lock"),
                patch("core.pcr_setup.find_pcr_target", return_value="emulator-5556") as target,
                patch("core.pcr_backend.check_pcr"),
                patch("core.pcr_backend.run_pcr") as run,
            ):
                self.assertTrue(self.agent.DailyClearPcr().run(context, None))
            target.assert_called_once_with(adb, "emulator-5556")
            game, command = run.call_args.args
            self.assertEqual(game.options["_pcr_runtime_config"], {
                "Extra": {"adb_path": str(adb), "adb_serial": "emulator-5556", "dnpath": ""},
                "Gift": {"auto_dismantle": False},
                "Task": {1: [["get_quest_reward"], ["get_gift", True]]},
            })
            context.tasker.stopping = True
            self.assertTrue(command.keywords["cancelled"]())
            log = log_path.read_text(encoding="utf-8")
            self.assertIn("ADB 设备 emulator-5556 已就绪", log)
            self.assertIn("公主连结日常完成", log)

    def test_preflight_failure_stays_in_log_after_returning_to_automas(self):
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "logs" / "pcr-automas.log"
            with (
                patch.object(self.agent, "LOG_PATH", log_path),
                patch.object(self.agent, "launch", side_effect=ValueError("模拟器里未安装公主连结 B 服")),
            ):
                self.assertFalse(self.agent.DailyClearPcr().run(None, None))
            self.assertIn("公主连结运行失败：模拟器里未安装公主连结 B 服", log_path.read_text(encoding="utf-8"))

    def test_empty_tasks_do_not_start_the_game(self):
        from core.pcr_setup import PCR_DAILY_TASKS

        with self.assertRaisesRegex(ValueError, "至少勾选一项"):
            self.agent.selected_tasks(self.context("adb", set()), PCR_DAILY_TASKS)
