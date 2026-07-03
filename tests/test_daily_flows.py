import unittest

from games.adapters import MockFlowContext
from games.flow import StepOutcome
from games.honkai3.flow import (
    HONKAI3_DAILY_FLOW,
    STEP_CLAIM_MAIL,
    STEP_MATERIAL_EXPEDITION,
    STEP_SIM_BATTLE_REDUCE,
)
from games.pcr.flow import (
    PCR_DAILY_FLOW,
    STEP_COLLECT_GIFTS,
    STEP_GUILD_DONATE,
    STEP_SWEEP,
)


class TestHonkai3DailyFlow(unittest.TestCase):
    def test_runs_enabled_steps_in_order(self):
        ctx = MockFlowContext(
            enabled_steps={step.step_id for step in HONKAI3_DAILY_FLOW.steps}
        )
        report = HONKAI3_DAILY_FLOW.run(ctx)

        self.assertTrue(report.success)
        self.assertEqual(len(HONKAI3_DAILY_FLOW.steps), len(report.steps))
        self.assertEqual(
            [step.step_id for step in HONKAI3_DAILY_FLOW.steps],
            [step.step_id for step in report.steps],
        )
        self.assertTrue(any("开始: 材料远征" in log for log in ctx.logs))

    def test_disabled_steps_are_skipped(self):
        enabled = {step.step_id for step in HONKAI3_DAILY_FLOW.steps}
        enabled.discard(STEP_SIM_BATTLE_REDUCE)
        enabled.discard(STEP_CLAIM_MAIL)

        ctx = MockFlowContext(enabled_steps=enabled)
        report = HONKAI3_DAILY_FLOW.run(ctx)

        outcomes = {step.step_id: step.outcome for step in report.steps}
        self.assertEqual(StepOutcome.SKIPPED, outcomes[STEP_SIM_BATTLE_REDUCE])
        self.assertEqual(StepOutcome.SKIPPED, outcomes[STEP_CLAIM_MAIL])
        self.assertEqual(StepOutcome.SUCCESS, outcomes[STEP_MATERIAL_EXPEDITION])

    def test_missing_feature_skips_non_critical_step(self):
        ctx = MockFlowContext(
            enabled_steps={STEP_MATERIAL_EXPEDITION},
            default_feature_present=False,
        )
        report = HONKAI3_DAILY_FLOW.run(ctx)

        outcomes = {step.step_id: step.outcome for step in report.steps}
        self.assertEqual(StepOutcome.SKIPPED, outcomes[STEP_MATERIAL_EXPEDITION])


class TestPcrDailyFlow(unittest.TestCase):
    def test_runs_all_mvp_steps(self):
        ctx = MockFlowContext(enabled_steps={step.step_id for step in PCR_DAILY_FLOW.steps})
        report = PCR_DAILY_FLOW.run(ctx)

        self.assertTrue(report.success)
        self.assertEqual(6, report.completed_count)
        self.assertIn("feature:pcr_gift_box", ctx.clicks)

    def test_sweep_can_be_disabled(self):
        enabled = {step.step_id for step in PCR_DAILY_FLOW.steps}
        enabled.discard(STEP_SWEEP)
        enabled.discard(STEP_GUILD_DONATE)

        ctx = MockFlowContext(enabled_steps=enabled)
        report = PCR_DAILY_FLOW.run(ctx)

        outcomes = {step.step_id: step.outcome for step in report.steps}
        self.assertEqual(StepOutcome.SKIPPED, outcomes[STEP_SWEEP])
        self.assertEqual(StepOutcome.SKIPPED, outcomes[STEP_GUILD_DONATE])
        self.assertEqual(StepOutcome.SUCCESS, outcomes[STEP_COLLECT_GIFTS])

    def test_dungeon_support_clicks_borrow(self):
        from games.pcr.flow import STEP_DUNGEON_SUPPORT

        ctx = MockFlowContext(enabled_steps={STEP_DUNGEON_SUPPORT})
        ctx.feature_hits = {
            "pcr_dungeon_entry": True,
            "pcr_support_borrow": True,
            "pcr_ok_button": True,
        }
        report = PCR_DAILY_FLOW.run(ctx)

        outcomes = {step.step_id: step.outcome for step in report.steps}
        self.assertEqual(StepOutcome.SUCCESS, outcomes[STEP_DUNGEON_SUPPORT])
        self.assertIn("feature:pcr_support_borrow", ctx.clicks)


if __name__ == "__main__":
    unittest.main()
