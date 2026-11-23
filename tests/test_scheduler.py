import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from core.config_loader import DEFAULT_LOCAL_CONFIG_PATH, GameConfig, HubConfig, load_hub_config
from core.native import run_native
from core.scheduler import RunAborted, _run_native, run_command, run_queue
from core.templates import check_templates
from main import main


class TestScheduler(unittest.TestCase):
    def test_queue_reports_failure_and_continues(self):
        game_ids = ("pcr", "honkai3")
        hub = load_hub_config()
        with patch("core.scheduler.check_game"), patch("core.scheduler._run_native") as execute:
            execute.side_effect = [ValueError("识别失败"), None]
            self.assertFalse(run_queue(hub, game_ids))
            self.assertEqual(list(game_ids), [call.args[0] for call in execute.call_args_list])

    def test_external_timeout_aborts_queue(self):
        game = GameConfig("星铁", True, "march7th", 2, {})
        hub = HubConfig({"starrail": game}, ("starrail",))
        with (
            patch("core.scheduler.check_game"),
            patch("core.scheduler._run_march7th", side_effect=subprocess.TimeoutExpired("m7a", 2)),
            self.assertRaises(RunAborted),
        ):
            run_queue(hub, hub.order)

    def test_pcr_queue_runs_upstream_without_hub_templates(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "pcrscript").mkdir()
            (project / "pcrscript" / "runtime.py").touch()
            (project / "images").mkdir()
            (project / "images" / "btn_ok.png").touch()
            config = project / "custom.yaml"
            config.write_text(
                "Extra:\n  adb_path: " + json.dumps(sys.executable) + "\nTask: {1: [[schedule]]}\n",
                encoding="utf-8",
            )
            (project / "daily_task.py").write_text(
                "import json, sys\n"
                "from pathlib import Path\n"
                "assert sys.argv[1] == '--config' and Path(sys.argv[2]).name == 'custom.yaml'\n"
                "print(json.dumps({'status': 'complete', 'verified': True, "
                "'tasks': [{'task': 'schedule', 'status': 'already_complete'}]}, indent=2))\n",
                encoding="utf-8",
            )
            game = GameConfig("公主连结", True, "pcr_script", 10, {
                "project_dir": str(project),
                "executable": sys.executable,
                "pcr_config": str(config),
            })
            hub = HubConfig({"pcr": game}, ("pcr",))
            self.assertTrue(run_queue(hub, hub.order))

    def test_native_worker_gets_snapshot_and_nonzero_is_failure(self):
        observed = {}

        def fail_worker(command, cwd, timeout):
            data = json.loads(Path(command[-1]).read_text(encoding="utf-8"))
            observed.update(data)
            return 1

        game = load_hub_config().games["endfield"]
        with patch("core.scheduler.run_command", side_effect=fail_worker):
            with self.assertRaisesRegex(ValueError, "未完成"):
                _run_native("endfield", game)
        self.assertEqual(game.options, observed["options"])

    def test_native_worker_rejects_missing_report_even_when_ok_script_returns_true(self):
        game = load_hub_config().games["endfield"]
        task = SimpleNamespace(report=None, failure=None)
        app = Mock()
        app.get_onetime_task.return_value = task
        app.run_task.return_value = True
        fake_task = SimpleNamespace(DailyClearTask=type(task))
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / "request.json"
            request.write_text(json.dumps(asdict(game)), encoding="utf-8")
            with (
                patch.dict(sys.modules, {"src.tasks.DailyClearTask": fake_task}),
                patch("core.native.check_game"),
                patch("core.native.open_profile", return_value=app),
                self.assertRaisesRegex(RuntimeError, "没有返回完整"),
            ):
                run_native("endfield", request)
        app.quit.assert_called_once()

    def test_process_exit_and_timeout(self):
        cwd = Path.cwd()
        self.assertEqual(2, run_command([sys.executable, "-c", "raise SystemExit(2)"], cwd, 10))
        with self.assertRaises(subprocess.TimeoutExpired):
            run_command([sys.executable, "-c", "import time; time.sleep(10)"], cwd, 1)

    def test_process_cancellation(self):
        with self.assertRaisesRegex(RunAborted, "任务已取消"):
            run_command(
                [sys.executable, "-c", "import time; time.sleep(10)"], Path.cwd(), 10, cancelled=lambda: True,
            )

    def test_plan_works_without_ok_script_or_templates(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing_local = str(Path(tmp) / DEFAULT_LOCAL_CONFIG_PATH.name)
            self.assertEqual(0, main(["--config", missing_local, "plan", "--features", "endfield"]))
            self.assertEqual(1, main(["--config", missing_local, "check", "endfield"]))


class TestTemplates(unittest.TestCase):
    def test_requires_annotation_and_referenced_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "templates.json"
            data = {
                "images": [{"id": 2, "file_name": "frame.png", "width": 100, "height": 100}],
                "categories": [{"id": 1, "name": "home"}],
                "annotations": [],
            }
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "找不到模板截图"):
                check_templates(path, {"home"})
            (root / "frame.png").touch()
            with self.assertRaisesRegex(ValueError, "缺少模板标注"):
                check_templates(path, {"home"})
            data["annotations"].append({"image_id": 2, "category_id": 1, "bbox": [1, 1, 3, 4]})
            path.write_text(json.dumps(data), encoding="utf-8")
            check_templates(path, {"home"})
