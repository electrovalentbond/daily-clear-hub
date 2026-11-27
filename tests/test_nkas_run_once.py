import contextlib
from datetime import datetime, timedelta
import importlib.util
import io
from pathlib import Path
import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "integrations" / "nkas-automas" / "run_once.py"
SPEC = importlib.util.spec_from_file_location("nkas_run_once", SCRIPT)
RUN_ONCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN_ONCE)


class FiniteNkasTests(unittest.TestCase):
    def invoke(self, *, due=True, serial=False, cold=False, outcomes=("complete",)):
        events = []
        outcomes = iter(outcomes)
        now = datetime.now()
        task = SimpleNamespace(command="Reward", next_run=now - timedelta(minutes=1), enabled=True)
        device = SimpleNamespace(app_is_running=lambda: not cold)

        class Config:
            Client_Platform = "adb"
            SCHEDULER_PRIORITY = "Restart > Reward"

            def get_next_task(self):
                self.pending_task = [task] if task.enabled and task.next_run < datetime.now() else []
                self.waiting_task = [task] if task.enabled and not self.pending_task else []

        class NativeScheduler:
            def __init__(self, config_name):
                self.config_name = config_name
                self.config = Config()
                self.device = device

            def loop(self):
                try:
                    self._loop()
                finally:
                    events.append("driver_release")

            def _loop(self):
                while True:
                    self.run(self.get_next_task().lower())

            def get_next_task(self):
                self.config.task = self.config.pending_task[0]
                return self.config.task.command

            def is_independent_task(self, command):
                return False

            def start(self):
                events.append("login")

            def run(self, command, skip_first_screenshot=False):
                events.append(command)
                outcome = next(outcomes)
                if outcome in {"complete", "lost"}:
                    task.next_run = now + timedelta(days=1)
                if outcome == "disable":
                    task.enabled = False
                if outcome == "login":
                    self.start()
                if outcome == "interrupt":
                    raise KeyboardInterrupt
                return outcome not in {"retry", "lost"}

            def _post_action(self):
                events.append("post_action")

        if not due:
            task.next_run = now + timedelta(days=1)
        modules = {
            "main": {"NikkeAutoScript": NativeScheduler},
            "module.base.resource": {"release_resources": lambda: events.append("release_resources")},
            "module.config.serial_state": {
                "read_serial_config": lambda: SimpleNamespace(enable=serial, group=["nkas"]),
            },
        }
        for name, attributes in modules.items():
            module = ModuleType(name)
            module.__dict__.update(attributes)
            modules[name] = module

        output = io.StringIO()
        with (
            patch.dict(sys.modules, modules),
            patch.object(sys, "path", sys.path.copy()),
            patch.object(sys, "argv", [str(SCRIPT)]),
            patch.object(RUN_ONCE, "validate_profile"),
            contextlib.redirect_stdout(output),
        ):
            result = RUN_ONCE.main(["nkas"])
        self.assertEqual(events[-3:], ["post_action", "release_resources", "driver_release"])
        return result, output.getvalue().splitlines(), events[:-3]

    def test_none_due_does_not_access_game(self):
        result, output, events = self.invoke(due=False)
        self.assertEqual((result, output[-1], events), (0, "DCH_NKAS_STATUS already_complete", []))

    def test_cold_adb_starts_before_due_task(self):
        result, output, events = self.invoke(cold=True)
        self.assertEqual((result, output[-1], events), (0, "DCH_NKAS_STATUS complete", ["login", "reward"]))

    def test_login_screen_and_native_retry_do_not_show_false_success(self):
        result, output, events = self.invoke(outcomes=("login", "retry", "complete"))
        self.assertEqual(result, 0)
        self.assertEqual(output.count("DCH_NKAS_STATUS task_retry Reward"), 2)
        self.assertEqual(events, ["reward", "login", "reward", "reward"])

    def test_unresolved_task_disappearing_from_queue_is_failure(self):
        result, output, _ = self.invoke(outcomes=("lost",))
        self.assertEqual(result, 1)
        self.assertTrue(output[-1].startswith("DCH_NKAS_STATUS failed "))

    def test_task_can_disable_itself_at_completion(self):
        result, output, _ = self.invoke(outcomes=("disable",))
        self.assertEqual((result, output[-1]), (0, "DCH_NKAS_STATUS complete"))

    def test_repeated_success_left_pending_is_bounded(self):
        result, output, events = self.invoke(outcomes=("repeat",) * 3)
        self.assertEqual(result, 1)
        self.assertTrue(output[-1].startswith("DCH_NKAS_STATUS failed Reward "))
        self.assertEqual(events, ["reward"] * 3)

    def test_serial_mode_rejected_before_controlling_game(self):
        result, output, events = self.invoke(serial=True)
        self.assertEqual((result, events), (1, []))
        self.assertIn("串行模式", output[-1])

    def test_interrupt_cleans_up_and_is_not_success(self):
        result, output, _ = self.invoke(outcomes=("interrupt",))
        self.assertEqual((result, output[-1]), (130, "DCH_NKAS_STATUS stopped"))

    def test_invalid_profile_does_not_load_upstream(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = RUN_ONCE.main([".."])
        self.assertEqual(result, 1)
        self.assertIn("实例名无效", output.getvalue())


if __name__ == "__main__":
    unittest.main()
