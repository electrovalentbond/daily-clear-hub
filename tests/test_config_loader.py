import tempfile
import unittest
from pathlib import Path

import yaml

from core.config_loader import enabled_games_in_order, load_hub_config


class TestConfigLoader(unittest.TestCase):
    def test_load_and_merge_local_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.yaml"
            local_path = root / "config.local.yaml"
            config_path.write_text(
                yaml.safe_dump(
                    {
                        "schedule_order": ["honkai3", "pcr"],
                        "games": {
                            "honkai3": {"enabled": True, "tasks": ["daily"]},
                            "pcr": {"enabled": False, "tasks": ["daily"]},
                        },
                    }
                ),
                encoding="utf-8",
            )
            local_path.write_text(
                yaml.safe_dump({"games": {"pcr": {"enabled": True}}}),
                encoding="utf-8",
            )

            hub = load_hub_config(config_path, local_path)
            ordered = enabled_games_in_order(hub)

            self.assertEqual(["honkai3", "pcr"], [game_id for game_id, _ in ordered])
            self.assertTrue(hub.games["pcr"].enabled)

    def test_project_config_exists(self):
        from core.config_loader import DEFAULT_CONFIG_PATH

        self.assertTrue(DEFAULT_CONFIG_PATH.exists())


if __name__ == "__main__":
    unittest.main()
