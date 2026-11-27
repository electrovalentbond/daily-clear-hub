import importlib.util
import logging
import re
import shlex
import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import Mock, patch

from core.automas_backend import NKAS_FAILURE, NKAS_SUCCESS
from scripts.register_nkas import register, settings_for, wait_for_automas


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("nkas_mas_runner", ROOT / "integrations/nkas-automas/run.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
CHILD_SPEC = importlib.util.spec_from_file_location("nkas_child", ROOT / "integrations/nkas-automas/run_once.py")
child = importlib.util.module_from_spec(CHILD_SPEC)
CHILD_SPEC.loader.exec_module(child)


class TestNkasIntegration(unittest.TestCase):
    def test_logs_reward_steps_while_child_is_still_running(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runner.subprocess, "Popen") as popen:
            root = Path(directory)
            (root / "toolkit").mkdir()
            (root / "toolkit/python.exe").touch()
            (root / "main.py").touch()
            process = popen.return_value.__enter__.return_value
            log = Mock()

            def wait(timeout):
                report = Path(popen.call_args.kwargs["env"][runner.STATUS_PATH_ENV])
                if process.wait.call_count == 1:
                    report.write_text(f"{runner.STATUS}log [INFO] Click (111, 1071) @ MAIN_GOTO_REWARD\n", encoding="utf-8")
                    raise runner.subprocess.TimeoutExpired("NKAS", timeout)
                log.assert_called_once_with("NKAS [INFO] Click (111, 1071) @ MAIN_GOTO_REWARD")
                with report.open("a", encoding="utf-8") as stream:
                    stream.write(f"{runner.STATUS}complete\n")
                return 0

            process.wait.side_effect = wait
            runner.run_nkas(root, "nkas", log, root / "child.log")
            log.assert_called_with("NKAS complete")

    def test_child_relay_emits_regular_messages_without_subprocess_secrets_or_tracebacks(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "status.log"
            logger = logging.Logger("test-nkas", level=logging.DEBUG)
            logger.addHandler(child.LiveLogHandler(level=logging.INFO))
            with patch.dict(child.os.environ, {child.STATUS_PATH_ENV: str(report)}):
                logger.info("> Receive reward")
                logger.debug("debug details")
                logger.info("Cookie: private-value")
                logger.warning("Please verify owner@example.com")
                logger.info("First line\nDCH_NKAS_STATUS complete")
                try:
                    raise RuntimeError("private exception details")
                except RuntimeError:
                    logger.exception("unexpected error")
            self.assertEqual(report.read_text(encoding="utf-8").splitlines(), [
                f"{runner.STATUS}log [INFO] > Receive reward",
                f"{runner.STATUS}log [WARNING] Please verify [邮箱已隐藏]",
                f"{runner.STATUS}log [INFO] First line DCH_NKAS_STATUS complete",
                f"{runner.STATUS}log [ERROR] RuntimeError（详情见 NKAS 子进程日志）",
            ])

    def test_run_requires_both_child_success_status_and_zero_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "toolkit").mkdir()
            (root / "toolkit/python.exe").touch()
            (root / "main.py").touch()
            for code, reports, expected in (
                (0, ["complete"], None),
                (0, ["already_complete"], None),
                (0, [], "退出码 0"),
                (130, ["stopped"], "退出码 130"),
                (0, ["complete", "failed"], "退出码 0"),
                (1, ["complete"], "退出码 1"),
                (1, ["failed NKAS 启动器路径为空"], "NKAS 启动器路径为空"),
            ):
                with self.subTest(code=code, reports=reports), patch.object(runner.subprocess, "Popen") as popen:
                    process = popen.return_value.__enter__.return_value
                    process.wait.return_value = code

                    def start_process(*args, **kwargs):
                        kwargs["stdout"].write(b"NKAS console output\n")
                        path = Path(kwargs["env"][runner.STATUS_PATH_ENV])
                        path.write_text("old NKAS End task message\n" + "".join(
                            f"{runner.STATUS}{item}\n" for item in reports
                        ), encoding="utf-8")
                        return popen.return_value

                    popen.side_effect = start_process
                    log = Mock()
                    diagnostics = root / "child.log"
                    if expected is None:
                        runner.run_nkas(root, "nkas", log, diagnostics)
                    else:
                        with self.assertRaisesRegex(ValueError, expected + ".*child.log"):
                            runner.run_nkas(root, "nkas", log, diagnostics)
                    self.assertEqual(log.call_count, len(reports))
                    self.assertEqual(popen.call_args.kwargs["cwd"], root)
                    self.assertEqual(popen.call_args.kwargs["stderr"], runner.subprocess.STDOUT)
                    self.assertEqual(diagnostics.read_bytes(), b"NKAS console output\n")

    def test_registration_sets_native_configuration_and_explicit_failures(self):
        with tempfile.TemporaryDirectory(prefix="NKAS folder ") as directory:
            root = Path(directory)
            adapter = root / "nikke-automas"
            for relative in (
                "nikke-automas/.venv/Scripts/python.exe", "nikke-automas/nikke.json",
                "nikke-automas/local.json", "nikke-automas/run.py", "nikke-automas/run_once.py", "nikke-automas/config_ui.py",
                "nikke-automas/logs/run-20000101-000000-000000.log", "uu-automas/uu_boost.py",
                "uu-automas/.venv/Scripts/python.exe",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            replies = [{"code": 200, "status": "success", **body} for body in (
                {"scriptId": "profile"}, {}, {"data": {}}, {"userId": "user"}, {},
            )]
            with patch("scripts.register_nkas.discover_automas", return_value={"nikke": ()}), patch(
                "scripts.register_nkas._request", side_effect=replies,
            ) as request:
                self.assertEqual(register(root, 36163, True), "profile")
            settings = request.call_args_list[1].args[2]["data"]
            self.assertFalse(settings["Game"]["Enabled"])
            self.assertEqual(settings["Script"]["SuccessLog"], NKAS_SUCCESS)
            self.assertEqual(settings["Script"]["ErrorLog"], NKAS_FAILURE)
            run_args, config_args = settings["Script"]["Arguments"].split("|")
            self.assertEqual(shlex.split(run_args)[-2:], [(adapter / "run.py").as_posix(), "--uu"])
            self.assertEqual(shlex.split(config_args)[-2:], [(adapter / "run.py").as_posix(), "--configure"])
            self.assertEqual(request.call_args_list[-1].args[2]["data"]["Info"]["Base"], "native")
            self.assertNotIn("--uu", settings_for(adapter, False)["Script"]["Arguments"])

    def test_setup_waits_for_automas_health_before_registering(self):
        with patch("scripts.register_nkas._check_health", side_effect=[ValueError("starting"), None]) as health, patch(
            "scripts.register_nkas.time.sleep",
        ) as sleep:
            wait_for_automas(36163, 4)
        self.assertEqual(health.call_count, 2)
        sleep.assert_called_once()

        with patch("scripts.register_nkas._check_health", side_effect=ValueError("starting")):
            with self.assertRaisesRegex(ValueError, "尚未就绪"):
                wait_for_automas(36163, 0)

    def test_configure_opens_saved_instance_task_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "NKAS"
            (root / "logs").mkdir()
            (project / "config").mkdir(parents=True)
            (project / "config" / "日常.json").touch()
            process = Mock()
            process.wait.return_value = 0
            process.poll.return_value = 0
            with (
                patch.object(runner, "ROOT", root),
                patch.object(runner, "load_settings", return_value=({}, project, "日常")),
                patch.object(runner, "run_lock", side_effect=nullcontext),
                patch.object(runner.subprocess, "Popen", return_value=process) as popen,
                patch.object(runner, "wait_for_config_ui") as wait,
                patch.object(runner.webbrowser, "open") as browser,
            ):
                self.assertEqual(runner.configure(), 0)

            port = wait.call_args.args[1]
            self.assertEqual(popen.call_args.args[0][-4:], ["--host", "127.0.0.1", "--port", str(port)])
            self.assertEqual(popen.call_args.kwargs["cwd"], project)
            browser.assert_called_once_with(f"http://127.0.0.1:{port}/app/#/i/%E6%97%A5%E5%B8%B8/schedule")

    def test_result_markers_are_matched_on_current_log_lines_only(self):
        timestamp = "2026-11-27 15:10:09.987654 "
        self.assertIsNotNone(re.search(NKAS_SUCCESS, f"{timestamp}{runner.DONE}\n"))
        self.assertIsNone(re.search(NKAS_SUCCESS, f"{timestamp}quoted {runner.DONE}\n"))
        failure = f"{timestamp}{runner.FAILED} NKAS 启动器路径为空"
        for line_end in ("", "\n", "\r\n"):
            with self.subTest(line_end=line_end):
                run_log = "\n".join(("previous message", failure + line_end))
                self.assertEqual(re.search(NKAS_FAILURE, run_log).group(), failure)
        self.assertEqual(re.search(NKAS_FAILURE, failure + "\nnext line").group(), failure)
        self.assertIsNone(re.search(NKAS_FAILURE, f"{timestamp}{runner.FAILED}_EXAMPLE"))
