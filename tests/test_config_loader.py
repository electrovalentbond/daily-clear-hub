import tempfile
import unittest
from pathlib import Path

from core.config_loader import load_hub_config
from games.registry import load_flow
from src.config import make_profile


class TestConfigLoader(unittest.TestCase):
    def load_override(self, yaml_text):
        with tempfile.TemporaryDirectory() as tmp:
            local_path = Path(tmp) / "local.yaml"
            local_path.write_text(yaml_text, encoding="utf-8-sig")
            return load_hub_config(local_path)

    def test_defaults_cover_all_games_with_valid_steps(self):
        hub = self.load_override("")
        self.assertEqual(7, len(hub.games))
        self.assertEqual((), hub.select([]))
        self.assertEqual(7, len(hub.select([], include_disabled=True)))
        for game_id, game in hub.games.items():
            flow = load_flow(game_id)
            self.assertEqual(game_id, flow.game_id)
            self.assertEqual(len(flow.pages), len({page.step_id for page in flow.pages}))
            self.assertTrue(flow.select(game.steps()))
            self.assertTrue(all(page.route for page in flow.pages))

    def test_order_selection_and_local_override(self):
        hub = self.load_override(
            "schedule_order: [pcr, honkai3]\n"
            "games:\n"
            "  honkai3: {enabled: true, steps: [bh3_claim_mail]}\n"
            "  pcr: {enabled: true, adb_serial: '127.0.0.1:5555'}\n"
        )
        self.assertEqual(("pcr", "honkai3"), hub.select([]))
        self.assertEqual(("genshin", "pcr"), hub.select(["genshin", "pcr", "genshin"]))
        self.assertEqual(("bh3_claim_mail",), hub.games["honkai3"].steps())
        self.assertEqual("BH3.exe", hub.games["honkai3"].string("exe"))
        with self.assertRaisesRegex(ValueError, "未知游戏"):
            hub.select(["typo"])

    def test_rejects_invalid_config(self):
        invalid = (
            "games: {no_game: {enabled: true}}",
            "games: {pcr: {enabled: 'false'}}",
            "games: {pcr: {timeout_sec: -5}}",
            "schedule_order: [pcr, pcr]",
        )
        for example in invalid:
            with self.subTest(example=example), self.assertRaises(ValueError):
                self.load_override(example)

    def test_profiles_do_not_mix_capture_targets(self):
        hub = self.load_override("games: {pcr: {adb_serial: '127.0.0.1:5555'}}")
        desktop = make_profile("honkai3", hub.games["honkai3"])
        android = make_profile("pcr", hub.games["pcr"])
        self.assertEqual(["BH3.exe"], desktop["windows"]["exe"])
        self.assertNotIn("adb", desktop)
        self.assertNotIn("windows", android)
        self.assertEqual([], android["adb"]["packages"])
        self.assertNotEqual(desktop["config_folder"], android["config_folder"])
