import unittest

from games.bhxy2.flow import STEP_LABELS as BH2_LABELS
from games.genshin.flow import STEP_LABELS as GI_LABELS
from games.honkai3.flow import STEP_LABELS as BH3_LABELS
from games.pcr.flow import STEP_LABELS as PCR_LABELS
from games.starrail.flow import STEP_LABELS as SR_LABELS
from games.task_config import build_step_config
from games.zzz.flow import STEP_LABELS as ZZZ_LABELS


class TestGameTaskConfig(unittest.TestCase):
    def test_honkai3_step_toggles(self):
        step_config = build_step_config({"材料远征": False, "邮件领取": True}, BH3_LABELS)
        self.assertFalse(step_config["bh3_material_expedition"])
        self.assertTrue(step_config["bh3_claim_mail"])
        self.assertEqual(len(BH3_LABELS), len(step_config))

    def test_pcr_step_toggles(self):
        step_config = build_step_config({"扫荡关卡": False}, PCR_LABELS)
        self.assertFalse(step_config["pcr_sweep"])
        self.assertEqual(len(PCR_LABELS), len(step_config))

    def test_starrail_step_toggles(self):
        step_config = build_step_config({"消耗开拓力": False}, SR_LABELS)
        self.assertFalse(step_config["sr_spend_power"])
        self.assertEqual(5, len(step_config))

    def test_zzz_step_toggles(self):
        step_config = build_step_config({"营业刮卡": False}, ZZZ_LABELS)
        self.assertFalse(step_config["zzz_business"])
        self.assertEqual(5, len(step_config))

    def test_genshin_step_toggles(self):
        step_config = build_step_config({"尘歌壶领取": True}, GI_LABELS)
        self.assertTrue(step_config["gi_teapot"])
        self.assertEqual(5, len(step_config))

    def test_bhxy2_step_toggles(self):
        step_config = build_step_config({"活动领奖": False}, BH2_LABELS)
        self.assertFalse(step_config["bh2_event"])
        self.assertEqual(6, len(step_config))


if __name__ == "__main__":
    unittest.main()
