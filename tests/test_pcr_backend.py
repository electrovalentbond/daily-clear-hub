import io
import json
import subprocess
import sys
import unittest
from contextlib import contextmanager, nullcontext, redirect_stdout
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

import yaml

from core import pcr_automas_job
from core.config_loader import PROJECT_ROOT, GameConfig
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

    def runner(
        self, status="complete", task_status="complete", *, verified=True, code=0, omit_json=False, reasons=None,
    ):
        def run_command(command, cwd, timeout, *, stdout):
            self.assertEqual([
                str(self.python), "-X", "utf8", "-u", "daily_task.py", "--config", str(self.config),
            ], command)
            self.assertEqual(self.project, cwd)
            self.assertEqual(120, timeout)
            report = {
                "status": status, "verified": verified, "counts": {task_status: 1},
                "tasks": [{"task": "schedule", "index": 1, "status": task_status, "reasons": reasons}],
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

    def test_failed_task_shows_upstream_reason(self):
        with redirect_stdout(io.StringIO()) as output, self.assertRaises(ValueError):
            run_pcr(self.game, self.runner("partial", "blocked", verified=False, reasons=["找不到日程表入口"]))
        self.assertIn("schedule 失败原因：找不到日程表入口", output.getvalue())

    def test_missing_report_shows_last_upstream_output(self):
        with redirect_stdout(io.StringIO()) as output, self.assertRaisesRegex(ValueError, "未返回最终 JSON"):
            run_pcr(self.game, self.runner(omit_json=True))
        self.assertIn("pcr-script 输出：进入游戏首页", output.getvalue())

    def test_individual_rejects_multiple_tasks_before_launch(self):
        run_command = Mock()
        with self.assertRaisesRegex(ValueError, "恰好包含一项"):
            run_pcr(self.game, run_command, individual=True)
        run_command.assert_not_called()

    def test_individual_legacy_finished_requires_clean_exit_and_matching_task(self):
        game = replace(self.game, options={
            **self.game.options,
            "_pcr_runtime_config": {"Task": {1: [["quick_clean", 1]]}},
        })

        def execute(task="quick_clean", code=0, verified=False):
            def run_command(command, cwd, timeout, *, stdout):
                self.assertEqual(command[:6], [
                    str(self.python), "-X", "utf8", "-u",
                    str(PROJECT_ROOT / "core" / "pcr_automas_job.py"), "--config",
                ])
                self.assertTrue(Path(command[-1]).is_absolute())
                config = yaml.safe_load(Path(command[-1]).read_text(encoding="utf-8"))
                self.assertEqual(config["Task"], {1: [["quick_clean", 1]]})
                self.assertEqual((cwd, timeout), (self.project, 120))
                stdout.write(json.dumps({
                    "status": "finished", "verified": verified,
                    "tasks": [{"task": task, "status": "finished"}],
                }).encode("utf-8"))
                return code

            return run_command

        messages = []
        run_pcr(game, execute(), individual=True, log=messages.append)
        self.assertIn("执行结束，结果未核验", "\n".join(messages))
        with self.assertRaisesRegex(ValueError, "不匹配"):
            run_pcr(game, execute(task="arena"), individual=True, log=messages.append)
        for run_command in (execute(code=2), execute(verified=True)):
            with self.assertRaisesRegex(ValueError, "未全部核实完成"):
                run_pcr(game, run_command, individual=True, log=messages.append)


class TestPCRIndividualJob(unittest.TestCase):
    def test_schedule_searches_below_notification_rows(self):
        notifications, schedule = object(), object()
        ui = Mock(last=notifications, spec=["scrollbar_bounds", "scrollbar", "last"])
        ui.scrollbar_bounds.return_value = (98, 222)
        task = SimpleNamespace(book=lambda _: True, completion=lambda view: (0, 7) if view is schedule else None, ui=ui)

        def scroll(screen, roi, direction, *, reached, content_distance, content_roi):
            self.assertIs(screen, notifications)
            self.assertEqual(roi, (769, 97, 784, 445))
            self.assertLess(content_distance, roi[3] - roi[1])
            self.assertEqual(content_roi, (195, 97, 765, 445))
            self.assertFalse(reached(notifications))
            if direction < 0:
                return False
            ui.last = schedule
            return reached(schedule)

        ui.scrollbar.side_effect = scroll
        self.assertIs(pcr_automas_job.restore_schedule_counter(task, notifications), schedule)
        self.assertEqual([item.args[2] for item in ui.scrollbar.call_args_list], [-1, 1])

    def test_schedule_stops_scrolling_when_book_or_track_is_unverified(self):
        for book, track in ((False, (98, 222)), (True, None)):
            with self.subTest(book=book, track=track):
                screen = object()
                ui = Mock(last=screen)
                ui.scrollbar_bounds.return_value = track
                task = SimpleNamespace(book=lambda _: book, completion=lambda _: None, ui=ui)
                self.assertIs(pcr_automas_job.restore_schedule_counter(task, screen), screen)
                ui.scrollbar.assert_not_called()

    def test_schedule_failure_report_is_printed_before_session_exit(self):
        class ADBDriver:
            adb_path = "adb.exe"
            device_name = "emulator-5556"

        class Schedule:
            pass

        @contextmanager
        def failed_session(_):
            yield
            raise SystemExit(1)

        report = {"status": "error", "verified": False, "tasks": [{"task": "schedule", "status": "error"}]}
        runtime = SimpleNamespace(
            load_config=Mock(return_value={"Task": {1: [["schedule"]]}, "Extra": {"adb_serial": "emulator-5556"}}),
            print_report=Mock(side_effect=SystemExit(2)),
            run_script=Mock(return_value=report),
            select_driver=Mock(return_value=ADBDriver()),
            summarize_daily=Mock(),
        )
        modules = {
            "pcrscript.driver": SimpleNamespace(ADBDriver=ADBDriver),
            "pcrscript.run_session": SimpleNamespace(RunSession=failed_session, daily_result=Mock()),
            "pcrscript.runtime": runtime,
            "pcrscript.tasks": SimpleNamespace(TimeLimitTask=type("TimeLimitTask", (), {}), find_taskclass=lambda _: Schedule),
        }
        with (
            patch.dict(sys.modules, modules),
            patch.object(sys, "path", sys.path.copy()),
            patch.object(pcr_automas_job.subprocess, "run"),
            self.assertRaises(SystemExit) as exit_status,
        ):
            pcr_automas_job.main(["--config", "profile.yml"])
        self.assertEqual(exit_status.exception.code, 1)
        self.assertIs(Schedule.restore_counter, pcr_automas_job.restore_schedule_counter)
        runtime.print_report.assert_called_once_with(report)

    def test_only_empty_temporal_results_are_converted_to_unavailable(self):
        class ADBDriver:
            adb_path = "adb.exe"
            device_name = "emulator-5554"

        class TimeLimitTask:
            pass

        task = "event"
        config = {"Task": {1: [[task]]}, "Extra": {"adb_serial": ADBDriver.device_name}}
        empty = {"status": "finished", "verified": False, "tasks": []}
        unavailable = {
            "status": "complete", "verified": True,
            "tasks": [{"task": task, "status": "unavailable"}],
        }
        for task_class, expected in ((TimeLimitTask, unavailable), (object, empty)):
            with self.subTest(task_class=task_class):
                result_writer = Mock()
                runtime = SimpleNamespace(
                    load_config=Mock(return_value=config),
                    print_report=Mock(),
                    run_script=Mock(return_value=empty),
                    select_driver=Mock(return_value=ADBDriver()),
                    summarize_daily=Mock(return_value=unavailable),
                )
                modules = {
                    "pcrscript.driver": SimpleNamespace(ADBDriver=ADBDriver),
                    "pcrscript.run_session": SimpleNamespace(
                        RunSession=Mock(return_value=nullcontext()), daily_result=result_writer,
                    ),
                    "pcrscript.runtime": runtime,
                    "pcrscript.tasks": SimpleNamespace(
                        TimeLimitTask=TimeLimitTask, find_taskclass=Mock(return_value=task_class),
                    ),
                }
                with (
                    patch.dict(sys.modules, modules),
                    patch.object(sys, "path", sys.path.copy()),
                    patch.object(pcr_automas_job.subprocess, "run") as adb,
                ):
                    pcr_automas_job.main(["--config", "profile.yml"])
                adb.assert_called_once_with(
                    ["adb.exe", "-s", "emulator-5554", "shell", "monkey", "-p", "com.bilibili.priconne", "1"],
                    stdin=subprocess.DEVNULL, check=True, timeout=15,
                )
                runtime.run_script.assert_called_once_with(config)
                runtime.print_report.assert_called_once_with(expected)
                if expected is unavailable:
                    result_writer.assert_called_once_with(unavailable)
                else:
                    result_writer.assert_not_called()
