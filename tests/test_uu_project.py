import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.dmm_project import OPTION_NAME as DMM_OPTION
from scripts.dmm_project import TASK_NAME as DMM_TASK
from scripts.dmm_project import prepare as prepare_dmm
from scripts.uu_project import (
    LAUNCH_OPTION, OPTION_NAME, PROJECTS, TASK_NAME, boost_arguments, prepare, run_pretask,
)


class UuProjectTest(unittest.TestCase):
    def test_variant_retains_original_tasks_and_gets_its_own_project_identity(self):
        interface = {
            "name": "Upstream",
            "version": "v1.0",
            "github": "https://github.com/upstream/project",
            "mirrorchyan_rid": "Upstream",
            "import": ["tasks.json"],
            "pretask": {"name": "StartGame", "exec": "something"},
            "option": {"Daily": {"type": "select"}},
            "task": [{"name": "Claim", "entry": "Claim"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            source = parent / "upstream.json"
            source.write_text(json.dumps(interface), encoding="utf-8-sig")
            for game, (name, _) in PROJECTS.items():
                with self.subTest(game=game):
                    target = parent / "interface.json"
                    prepare(game, source, target, parent / "python.exe", parent / "uu_project.py")
                    variant = json.loads(target.read_text(encoding="utf-8"))
                    self.assertEqual(variant["name"], name)
                    self.assertNotIn("github", variant)
                    self.assertNotIn("mirrorchyan_rid", variant)
                    self.assertEqual(variant["task"], interface["task"])
                    self.assertEqual(variant["import"], interface["import"])
                    self.assertEqual(variant["option"]["Daily"], interface["option"]["Daily"])
                    self.assertEqual(variant["pretask"][1:], [interface["pretask"]])
                    pretask = variant["pretask"][0]
                    self.assertEqual(pretask["name"], TASK_NAME)
                    self.assertEqual(pretask["exec"], "powershell")
                    self.assertEqual(pretask["option"], [OPTION_NAME, LAUNCH_OPTION])
                    self.assertEqual(pretask["args"][-2:], ["-DmmGame", game])
                    self.assertNotIn("default_check", pretask)
                    self.assertEqual(json.loads(source.read_text(encoding="utf-8-sig")), interface)

    def test_options_are_passed_as_data_and_require_a_target(self):
        exe = r"D:\Programs & Games\UU\uu_launcher.exe"
        options = {OPTION_NAME: {"game": "  NIKKE（国际服）  ", "region": "日服", "exe": exe}}
        self.assertEqual(boost_arguments(json.dumps(options)), ["--game=NIKKE（国际服）", "--region=日服", f"--exe={exe}"])
        with self.assertRaisesRegex(ValueError, "游戏全名"):
            boost_arguments(json.dumps({OPTION_NAME: {"game": " "}}))

    def test_launches_only_when_the_switch_is_enabled(self):
        for case in ("Yes", "No", True):
            with self.subTest(case=case):
                options = {OPTION_NAME: {"game": "学园偶像大师"}, LAUNCH_OPTION: case}
                expected = ["--game=学园偶像大师"]
                if case == "Yes":
                    expected.append("--launch-game")
                self.assertEqual(boost_arguments(json.dumps(options)), expected)

    def test_waits_for_dmm_window_after_uu_requests_launch(self):
        args = ["--game=学园偶像大师", "--launch-game"]
        project = Path("Project With Spaces")
        with patch("scripts.uu_project.boost", return_value=0) as boost, patch(
            "scripts.uu_project.subprocess.run"
        ) as run:
            run.return_value.returncode = 1
            self.assertEqual(run_pretask(args, "gakumas", project), 1)
        boost.assert_called_once_with(args)
        run.assert_called_once_with([
            "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
            "-File", str(project / "daily-clear-dmm.ps1"), "-Game", "gakumas", "-WaitOnly",
        ], check=False)

    def test_skips_window_wait_without_launch_or_on_uu_failure(self):
        for opts, code in ((["--game=game"], 0), (["--game=game", "--launch-game"], 1)):
            with self.subTest(opts=opts), patch("scripts.uu_project.boost", return_value=code), patch(
                "scripts.uu_project.subprocess.run"
            ) as run:
                self.assertEqual(run_pretask(opts, "dotabyss", Path("project")), code)
                run.assert_not_called()

    def test_dmm_launch_is_available_without_uu_and_runs_after_uu_in_the_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            for game, controller in (("gakumas", "PC"), ("dotabyss", "Win32Front")):
                with self.subTest(game=game):
                    source = parent / f"{game}.json"
                    upstream = {"name": "Upstream", "pretask": {"name": "Original"}, "task": [{"name": "Daily"}]}
                    source.write_text(json.dumps(upstream), encoding="utf-8-sig")

                    self.assertTrue(prepare_dmm(game, source))
                    installed = source.read_bytes()
                    self.assertFalse(prepare_dmm(game, source))
                    self.assertEqual(source.read_bytes(), installed)
                    regular = json.loads(installed)
                    launch, original = regular["pretask"]
                    self.assertEqual(original, upstream["pretask"])
                    self.assertEqual(regular["task"], upstream["task"])
                    self.assertEqual(launch["name"], DMM_TASK)
                    self.assertEqual(launch["controller"], [controller])
                    self.assertEqual(launch["args"][-3:], ["{PROJECT_DIR}/daily-clear-dmm.ps1", "-Game", game])
                    self.assertEqual(launch["option"], [DMM_OPTION])
                    self.assertEqual(regular["option"][DMM_OPTION]["inputs"][0]["default"], "")

                    target = parent / "interface.json"
                    prepare(game, source, target, parent / "python.exe", parent / "uu_project.py")
                    variant = json.loads(target.read_bytes())
                    self.assertEqual([task["name"] for task in variant["pretask"]], [TASK_NAME, DMM_TASK, "Original"])
                    self.assertEqual(variant["option"][LAUNCH_OPTION]["controller"], [controller])
                    self.assertEqual(variant["option"][LAUNCH_OPTION]["default_case"], "No")
                    self.assertEqual(source.read_bytes(), installed)
