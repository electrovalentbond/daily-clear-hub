from __future__ import annotations

from games.flow import DailyFlow, DailyStep
from games.starrail import steps

STEP_ENSURE_LOBBY = "sr_ensure_lobby"
STEP_ASSIGNMENTS = "sr_assignments"
STEP_SPEND_POWER = "sr_spend_power"
STEP_DAILY_TRAINING = "sr_daily_training"
STEP_CLAIM_MAIL = "sr_claim_mail"

DEFAULT_STEP_TOGGLES: dict[str, bool] = {
    STEP_ENSURE_LOBBY: True,
    STEP_ASSIGNMENTS: True,
    STEP_SPEND_POWER: True,
    STEP_DAILY_TRAINING: True,
    STEP_CLAIM_MAIL: True,
}

STARRAIL_DAILY_FLOW = DailyFlow(
    game_id="starrail",
    steps=[
        DailyStep(STEP_ENSURE_LOBBY, "回到大世界", steps.step_ensure_lobby),
        DailyStep(STEP_ASSIGNMENTS, "委托领取派遣", steps.step_claim_assignments),
        DailyStep(STEP_SPEND_POWER, "消耗开拓力", steps.step_spend_trailblaze_power),
        DailyStep(STEP_DAILY_TRAINING, "每日实训领奖", steps.step_claim_daily_training),
        DailyStep(STEP_CLAIM_MAIL, "邮件领取", steps.step_claim_mail),
    ],
)

STEP_LABELS: dict[str, str] = {step.step_id: step.name for step in STARRAIL_DAILY_FLOW.steps}
