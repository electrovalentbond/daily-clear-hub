import io
import json
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from core.config_loader import GameConfig
from core.pcr_backend import check_pcr, run_pcr


class TestPCRBackend(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.project = Path(directory.name).resolve()
        for relative in ("daily_task.py", "pcrscript/runtime.py", "images/btn_ok.png"):
            asset = self.project / relative
            asset.parent.mkdir(parents=True, exist_ok=True)
            asset.touch()
        self.python = self.project / "python.exe"
        self.python.touch()
        self.adb = self.project / "adb.exe"
        self.adb.touch()
        self.config = self.project / "daily_config.yml"
        self.config.write_text(yaml.safe_dump({
            "Extra": {"adb_path": "adb.exe", "adb_serial": "emulator-5554"},
            "Task": {1: [["schedule"], ["get_quest_reward"], ["get_gift", True]]},
        }), encoding="utf-8")
        self.game = GameConfig("公主连结", True, "pcr_script", 120, {
            "executable": str(self.python), "project_dir": str(self.project), "pcr_config": str(self.config),
        })

    def test_preflight_requires_assets_and_one_task_group(self):
        check_pcr(self.game)
        self.config.write_text("Task: {1: [[schedule]], 2: [[get_gift]]}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "保留一组"):
            check_pcr(self.game)
        (self.project / "images/btn_ok.png").unlink()
        with self.assertRaisesRegex(ValueError, "缺少 images/btn_ok.png"):
            check_pcr(self.game)

    def runner(self, status="complete", task_status="complete", *, verified=True, code=0, omit_json=False):
        def run_command(command, cwd, timeout, *, stdout):
            self.assertEqual([
                str(self.python), "-X", "utf8", "-u", "daily_task.py", "--config", str(self.config),
            ], command)
            self.assertEqual(self.project, cwd)
            self.assertEqual(120, timeout)
            report = {
                "status": status, "verified": verified, "counts": {task_status: 1},
                "tasks": [{"task": "schedule", "index": 1, "status": task_status}],
            }
            stdout.write("进入游戏首页\r\n".encode("utf-8"))
            if not omit_json:
                stdout.write(json.dumps(report, indent=2).encode("utf-8"))
            return code

        return run_command

    def test_checks_terminal_verification_and_surfaces_task_states(self):
        for status in ("complete", "already_complete", "unavailable"):
            with self.subTest(status=status), redirect_stdout(io.StringIO()) as output:
                run_pcr(self.game, self.runner(task_status=status))
                self.assertIn(f"schedule  {status}", output.getvalue())

    def test_does_not_trust_zero_exit_or_inconsistent_report(self):
        for kwargs in (
            {"status": "finished", "task_status": "finished", "verified": False},
            {"status": "partial", "task_status": "partial", "code": 2},
            {"task_status": "cancelled"},
            {"code": 1},
            {"omit_json": True},
        ):
            with self.subTest(kwargs=kwargs), redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
                run_pcr(self.game, self.runner(**kwargs))

    def test_timeout_propagates(self):
        def run_command(command, cwd, timeout, *, stdout):
            raise subprocess.TimeoutExpired(command, timeout)

        with self.assertRaises(subprocess.TimeoutExpired):
            run_pcr(self.game, run_command)
