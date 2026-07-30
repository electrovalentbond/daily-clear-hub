from __future__ import annotations

from games.bhxy2 import steps
from games.flow import DailyFlow, DailyStep

STEP_ENSURE_HOME = "bh2_ensure_home"
STEP_CHECKIN = "bh2_checkin"
STEP_ADVENTURE = "bh2_adventure"
STEP_SHOP = "bh2_shop"
STEP_MAIL = "bh2_mail"
STEP_EVENT = "bh2_event"

DEFAULT_STEP_TOGGLES: dict[str, bool] = {
    STEP_ENSURE_HOME: True,
    STEP_CHECKIN: True,
    STEP_ADVENTURE: True,
    STEP_SHOP: True,
    STEP_MAIL: True,
    STEP_EVENT: False,
}

BHXY2_DAILY_FLOW = DailyFlow(
    game_id="bhxy2",
    steps=[
        DailyStep(STEP_ENSURE_HOME, "回到主界面", steps.step_ensure_home),
        DailyStep(STEP_CHECKIN, "每日签到", steps.step_daily_checkin),
        DailyStep(STEP_ADVENTURE, "冒险扫荡", steps.step_adventure),
        DailyStep(STEP_SHOP, "商店免费领取", steps.step_shop_freebies),
        DailyStep(STEP_MAIL, "邮件领取", steps.step_claim_mail),
        DailyStep(STEP_EVENT, "活动领奖", steps.step_claim_event),
    ],
)

STEP_LABELS: dict[str, str] = {step.step_id: step.name for step in BHXY2_DAILY_FLOW.steps}
