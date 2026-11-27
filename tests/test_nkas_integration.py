import importlib.util
import re
import shlex
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from core.automas_backend import NKAS_FAILURE, NKAS_SUCCESS
from scripts.register_nkas import register, settings_for


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("nkas_mas_runner", ROOT / "integrations/nkas-automas/run.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class TestNkasIntegration(unittest.TestCase):
    def test_run_requires_both_child_success_status_and_zero_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "toolkit").mkdir()
            (root / "toolkit/python.exe").touch()
            (root / "main.py").touch()
            for code, reports, expected in (
                (0, ["complete"], True),
                (0, ["already_complete"], True),
                (0, [], False),
                (0, ["stopped"], False),
                (0, ["complete", "failed"], False),
                (1, ["complete"], False),
            ):
                with self.subTest(code=code, reports=reports), patch.object(runner.subprocess, "Popen") as popen:
                    process = popen.return_value.__enter__.return_value
                    process.wait.return_value = code

                    def start_process(*args, **kwargs):
                        path = Path(kwargs["env"][runner.STATUS_PATH_ENV])
                        path.write_text("old NKAS End task message\n" + "".join(
                            f"{runner.STATUS}{item}\n" for item in reports
                        ), encoding="utf-8")
                        return popen.return_value

                    popen.side_effect = start_process
                    log = Mock()
                    self.assertEqual(runner.run_nkas(root, "nkas", log), expected)
                    self.assertEqual(log.call_count, len(reports))
                    self.assertEqual(popen.call_args.kwargs["cwd"], root)

    def test_registration_sets_native_configuration_and_explicit_failures(self):
        with tempfile.TemporaryDirectory(prefix="NKAS folder ") as directory:
            root = Path(directory)
            adapter = root / "nikke-automas"
            for relative in (
                "nikke-automas/.venv/Scripts/python.exe", "nikke-automas/nikke.json",
                "nikke-automas/local.json", "nikke-automas/run.py", "nikke-automas/run_once.py",
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
            self.assertEqual(shlex.split(settings["Script"]["Arguments"])[-2:], [(adapter / "run.py").as_posix(), "--uu"])
            self.assertEqual(request.call_args_list[-1].args[2]["data"]["Info"]["Base"], "native")
            self.assertNotIn("--uu", settings_for(adapter, False)["Script"]["Arguments"])

    def test_result_markers_are_matched_on_current_log_lines_only(self):
        timestamp = "2026-11-27 15:10:09.987654 "
        self.assertIsNotNone(re.search(NKAS_SUCCESS, f"{timestamp}{runner.DONE}\n"))
        self.assertIsNone(re.search(NKAS_SUCCESS, f"{timestamp}quoted {runner.DONE}\n"))
        self.assertIsNotNone(re.search(NKAS_FAILURE, f"{timestamp}{runner.FAILED} NKAS 退出\n"))
