import json
import tempfile
import unittest
from pathlib import Path

from scripts.uu_project import OPTION_NAME, PROJECTS, TASK_NAME, boost_arguments, prepare


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
                    self.assertEqual(pretask["option"], [OPTION_NAME])
                    self.assertNotIn("default_check", pretask)
                    self.assertEqual(json.loads(source.read_text(encoding="utf-8-sig")), interface)

    def test_options_are_passed_as_data_and_require_a_target(self):
        exe = r"D:\Programs & Games\UU\uu_launcher.exe"
        options = {OPTION_NAME: {"game": "  NIKKE（国际服）  ", "region": "日服", "exe": exe}}
        self.assertEqual(boost_arguments(json.dumps(options)), ["--game=NIKKE（国际服）", "--region=日服", f"--exe={exe}"])
        with self.assertRaisesRegex(ValueError, "游戏全名"):
            boost_arguments(json.dumps({OPTION_NAME: {"game": " "}}))
