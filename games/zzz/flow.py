from __future__ import annotations

from games.flow import DailyFlow, DailyStep
from games.zzz import steps

STEP_ENSURE_LOBBY = "zzz_ensure_lobby"
STEP_BUSINESS = "zzz_business"
STEP_SPEND_BATTERY = "zzz_spend_battery"
STEP_DAILY_MISSIONS = "zzz_daily_missions"
STEP_CLAIM_MAIL = "zzz_claim_mail"

DEFAULT_STEP_TOGGLES: dict[str, bool] = {
    STEP_ENSURE_LOBBY: True,
    STEP_BUSINESS: True,
    STEP_SPEND_BATTERY: True,
    STEP_DAILY_MISSIONS: True,
    STEP_CLAIM_MAIL: True,
}

ZZZ_DAILY_FLOW = DailyFlow(
    game_id="zzz",
    steps=[
        DailyStep(STEP_ENSURE_LOBBY, "回到大厅", steps.step_ensure_lobby),
        DailyStep(STEP_BUSINESS, "营业刮卡", steps.step_business_scratch),
        DailyStep(STEP_SPEND_BATTERY, "消耗电量", steps.step_spend_battery),
        DailyStep(STEP_DAILY_MISSIONS, "每日任务领奖", steps.step_claim_daily_missions),
        DailyStep(STEP_CLAIM_MAIL, "邮件领取", steps.step_claim_mail),
    ],
)

STEP_LABELS: dict[str, str] = {step.step_id: step.name for step in ZZZ_DAILY_FLOW.steps}
