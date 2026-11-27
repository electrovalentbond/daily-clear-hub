import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "integrations" / "dotabyss-automas"


def load_adapter_module(name):
    spec = importlib.util.spec_from_file_location(f"dotabyss_{name}", PROJECT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestDotAbyssAutoMas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.dict(sys.modules, {
            "maa.agent.agent_server": SimpleNamespace(
                AgentServer=SimpleNamespace(custom_action=lambda _: lambda action: action)
            ),
            "maa.custom_action": SimpleNamespace(CustomAction=object),
        }):
            cls.agent = load_adapter_module("agent")
        cls.job = load_adapter_module("job")

    def test_auto_mas_tasks_match_upstream_and_default_to_reward_claims(self):
        interface = json.loads((PROJECT / "interface.json").read_text(encoding="utf-8"))
        pipeline = json.loads((PROJECT / "resource/pipeline/daily.json").read_text(encoding="utf-8"))
        tasks = {}
        for row in interface["task"]:
            action = pipeline[row["entry"]]["action"]["param"]
            self.assertEqual(action["custom_action"], "DailyClearDotAbyss")
            tasks[row["name"]] = action["custom_action_param"]["task"]
        self.assertEqual(set(tasks.values()), self.agent.TASKS)
        self.assertEqual(len(tasks), 7)
        self.assertEqual(
            [tasks[row["name"]] for row in interface["preset"][0]["task"] if row["enabled"]],
            ["claim_gifts_new", "claim_missions"],
        )
        self.assertNotIn("github", interface)

    def test_agent_requires_the_selected_task_and_valid_process_result(self):
        context = SimpleNamespace(tasker=SimpleNamespace(stopping=False, controller=SimpleNamespace(info={
            "type": "win32", "hwnd": 222,
        })))
        project = Path("/dotabyss")

        def make_command_run(task, status, code):
            def execute(command, cwd, timeout, stdout, stderr, cancelled):
                self.assertEqual(command[-3:-1], ["claim_missions", "222"])
                self.assertEqual(cwd, project)
                self.assertEqual(stdout, subprocess.DEVNULL)
                self.assertEqual(stderr, subprocess.DEVNULL)
                self.assertFalse(cancelled())
                Path(command[-1]).write_text(json.dumps({"task": task, "status": status}), encoding="utf-8")
                return code

            return execute

        with patch.object(self.agent, "installed_paths", return_value=(ROOT, project)):
            for task, status, code, expected in (
                ("claim_missions", "done", 0, "done"),
                ("claim_missions", "blocked", 0, "blocked"),
                ("other", "done", 0, ValueError),
                ("claim_missions", "done", 1, ValueError),
            ):
                with self.subTest(task=task, status=status, code=code), patch(
                    "core.scheduler.run_command", side_effect=make_command_run(task, status, code),
                ):
                    if expected is ValueError:
                        with self.assertRaises(ValueError):
                            self.agent.execute_task(context, "claim_missions")
                    else:
                        self.assertEqual(self.agent.execute_task(context, "claim_missions"), expected)

    def test_job_uses_only_the_bound_dmm_window_and_does_not_copy_model_output(self):
        class DeviceError(RuntimeError):
            pass

        class Brain:
            pass

        class GameDevice:
            def __init__(self):
                window = self._find_window("ドットアビスX")
                if window is None:
                    raise DeviceError("invalid window")
                self.hwnd = window.hwnd
                self.ctrl = SimpleNamespace(set_screenshot_use_raw_size=lambda enabled: enabled)

            def bring_to_front(self):
                pass

            def screenshot(self):
                return SimpleNamespace(shape=(720, 1280, 3))

        windows = [
            SimpleNamespace(hwnd=111, class_name="UnityWndClass", window_name="ドットアビスX"),
            SimpleNamespace(hwnd=222, class_name="UnityWndClass", window_name="ドットアビスX"),
            SimpleNamespace(hwnd=333, class_name="Chrome_WidgetWin_1", window_name="ドットアビスX"),
        ]
        run_selected = Mock(return_value=[{"task": "claim_gifts_new", "status": "done", "detail": "secret"}])
        fake_modules = {
            "dotabyss_agent.brain": SimpleNamespace(Brain=Brain),
            "dotabyss_agent.device": SimpleNamespace(
                GameDevice=GameDevice, DeviceError=DeviceError,
                Toolkit=SimpleNamespace(find_desktop_windows=lambda: windows),
            ),
            "dotabyss_agent.runner": SimpleNamespace(run_selected=run_selected),
            "openai": SimpleNamespace(OpenAIError=RuntimeError),
        }
        with tempfile.TemporaryDirectory() as directory, patch.dict(sys.modules, fake_modules), patch.object(
            sys, "path", sys.path.copy(),
        ):
            result = Path(directory) / "result.json"
            with patch.object(sys, "argv", ["job.py", "claim_gifts_new", "222", str(result)]):
                self.job.main()
            self.assertEqual(json.loads(result.read_text(encoding="utf-8")), {
                "task": "claim_gifts_new", "status": "done",
            })
            self.assertEqual(self.job.task_status("claim_gifts_new", 333), "window")
        run_selected.assert_called_once()
        self.assertEqual(run_selected.call_args.args, (["claim_gifts_new"],))
        self.assertEqual(run_selected.call_args.kwargs["_device"].hwnd, 222)
        self.assertIsInstance(run_selected.call_args.kwargs["_brain"], Brain)
        self.assertFalse(run_selected.call_args.kwargs["update_knowledge"])
