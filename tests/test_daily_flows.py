import unittest

from games.adapters import MockFlowContext
from games.bhxy2.flow import BHXY2_DAILY_FLOW, STEP_CHECKIN, STEP_EVENT
from games.flow import StepOutcome
from games.genshin.flow import GENSHIN_DAILY_FLOW, STEP_COMMISSIONS, STEP_TEAPOT
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
from games.starrail.flow import STARRAIL_DAILY_FLOW, STEP_DAILY_TRAINING, STEP_SPEND_POWER
from games.zzz.flow import ZZZ_DAILY_FLOW, STEP_BUSINESS, STEP_SPEND_BATTERY


def _run_all(flow):
    ctx = MockFlowContext(enabled_steps={step.step_id for step in flow.steps})
    return flow.run(ctx), ctx


class TestHonkai3DailyFlow(unittest.TestCase):
    def test_runs_enabled_steps_in_order(self):
        report, ctx = _run_all(HONKAI3_DAILY_FLOW)
        self.assertTrue(report.success)
        self.assertEqual(len(HONKAI3_DAILY_FLOW.steps), len(report.steps))
        self.assertTrue(any("开始: 材料远征" in log for log in ctx.logs))

    def test_disabled_steps_are_skipped(self):
        enabled = {step.step_id for step in HONKAI3_DAILY_FLOW.steps}
        enabled.discard(STEP_SIM_BATTLE_REDUCE)
        enabled.discard(STEP_CLAIM_MAIL)
        report = HONKAI3_DAILY_FLOW.run(MockFlowContext(enabled_steps=enabled))
        outcomes = {step.step_id: step.outcome for step in report.steps}
        self.assertEqual(StepOutcome.SKIPPED, outcomes[STEP_SIM_BATTLE_REDUCE])
        self.assertEqual(StepOutcome.SUCCESS, outcomes[STEP_MATERIAL_EXPEDITION])


class TestPcrDailyFlow(unittest.TestCase):
    def test_runs_all_mvp_steps(self):
        report, ctx = _run_all(PCR_DAILY_FLOW)
        self.assertTrue(report.success)
        self.assertEqual(6, report.completed_count)
        self.assertIn("feature:pcr_gift_box", ctx.clicks)

    def test_sweep_can_be_disabled(self):
        enabled = {step.step_id for step in PCR_DAILY_FLOW.steps}
        enabled.discard(STEP_SWEEP)
        enabled.discard(STEP_GUILD_DONATE)
        report = PCR_DAILY_FLOW.run(MockFlowContext(enabled_steps=enabled))
        outcomes = {step.step_id: step.outcome for step in report.steps}
        self.assertEqual(StepOutcome.SKIPPED, outcomes[STEP_SWEEP])
        self.assertEqual(StepOutcome.SUCCESS, outcomes[STEP_COLLECT_GIFTS])


class TestStarRailDailyFlow(unittest.TestCase):
    def test_mvp_order(self):
        report, ctx = _run_all(STARRAIL_DAILY_FLOW)
        self.assertTrue(report.success)
        self.assertEqual(5, report.completed_count)
        self.assertTrue(any("开始: 每日实训领奖" in log for log in ctx.logs))

    def test_disable_power_spend(self):
        enabled = {step.step_id for step in STARRAIL_DAILY_FLOW.steps}
        enabled.discard(STEP_SPEND_POWER)
        report = STARRAIL_DAILY_FLOW.run(MockFlowContext(enabled_steps=enabled))
        outcomes = {step.step_id: step.outcome for step in report.steps}
        self.assertEqual(StepOutcome.SKIPPED, outcomes[STEP_SPEND_POWER])
        self.assertEqual(StepOutcome.SUCCESS, outcomes[STEP_DAILY_TRAINING])


class TestZzzDailyFlow(unittest.TestCase):
    def test_mvp_order(self):
        report, ctx = _run_all(ZZZ_DAILY_FLOW)
        self.assertTrue(report.success)
        self.assertEqual(5, report.completed_count)
        self.assertIn("feature:zzz_business_entry", ctx.clicks)

    def test_disable_battery(self):
        enabled = {step.step_id for step in ZZZ_DAILY_FLOW.steps}
        enabled.discard(STEP_SPEND_BATTERY)
        report = ZZZ_DAILY_FLOW.run(MockFlowContext(enabled_steps=enabled))
        outcomes = {step.step_id: step.outcome for step in report.steps}
        self.assertEqual(StepOutcome.SKIPPED, outcomes[STEP_SPEND_BATTERY])
        self.assertEqual(StepOutcome.SUCCESS, outcomes[STEP_BUSINESS])


class TestGenshinDailyFlow(unittest.TestCase):
    def test_mvp_order(self):
        report, _ = _run_all(GENSHIN_DAILY_FLOW)
        self.assertTrue(report.success)
        self.assertEqual(5, len(report.steps))

    def test_teapot_default_off_when_disabled(self):
        enabled = {step.step_id for step in GENSHIN_DAILY_FLOW.steps}
        enabled.discard(STEP_TEAPOT)
        report = GENSHIN_DAILY_FLOW.run(MockFlowContext(enabled_steps=enabled))
        outcomes = {step.step_id: step.outcome for step in report.steps}
        self.assertEqual(StepOutcome.SKIPPED, outcomes[STEP_TEAPOT])
        self.assertEqual(StepOutcome.SUCCESS, outcomes[STEP_COMMISSIONS])


class TestBhxy2DailyFlow(unittest.TestCase):
    def test_mvp_order(self):
        report, ctx = _run_all(BHXY2_DAILY_FLOW)
        self.assertTrue(report.success)
        self.assertEqual(6, len(report.steps))
        self.assertTrue(any("开始: 每日签到" in log for log in ctx.logs))

    def test_event_can_be_disabled(self):
        enabled = {step.step_id for step in BHXY2_DAILY_FLOW.steps}
        enabled.discard(STEP_EVENT)
        report = BHXY2_DAILY_FLOW.run(MockFlowContext(enabled_steps=enabled))
        outcomes = {step.step_id: step.outcome for step in report.steps}
        self.assertEqual(StepOutcome.SKIPPED, outcomes[STEP_EVENT])
        self.assertEqual(StepOutcome.SUCCESS, outcomes[STEP_CHECKIN])


if __name__ == "__main__":
    unittest.main()
