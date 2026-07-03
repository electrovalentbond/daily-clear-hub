import unittest

from games.honkai3.flow import STEP_LABELS as BH3_LABELS
from games.pcr.flow import STEP_LABELS as PCR_LABELS
from games.task_config import build_step_config


class TestGameTaskConfig(unittest.TestCase):
    def test_honkai3_step_toggles(self):
        config = {"材料远征": False, "邮件领取": True}
        step_config = build_step_config(config, BH3_LABELS)

        self.assertFalse(step_config["bh3_material_expedition"])
        self.assertTrue(step_config["bh3_claim_mail"])
        self.assertEqual(len(BH3_LABELS), len(step_config))

    def test_pcr_step_toggles(self):
        config = {"扫荡关卡": False}
        step_config = build_step_config(config, PCR_LABELS)

        self.assertFalse(step_config["pcr_sweep"])
        self.assertEqual(len(PCR_LABELS), len(step_config))


if __name__ == "__main__":
    unittest.main()
