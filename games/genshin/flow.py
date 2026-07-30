from __future__ import annotations

from games.flow import DailyFlow, DailyStep
from games.genshin import steps

STEP_ENSURE_LOBBY = "gi_ensure_lobby"
STEP_COMMISSIONS = "gi_commissions"
STEP_RESIN_SWEEP = "gi_resin_sweep"
STEP_EXPEDITIONS = "gi_expeditions"
STEP_TEAPOT = "gi_teapot"

DEFAULT_STEP_TOGGLES: dict[str, bool] = {
    STEP_ENSURE_LOBBY: True,
    STEP_COMMISSIONS: True,
    STEP_RESIN_SWEEP: True,
    STEP_EXPEDITIONS: True,
    STEP_TEAPOT: False,
}

GENSHIN_DAILY_FLOW = DailyFlow(
    game_id="genshin",
    steps=[
        DailyStep(STEP_ENSURE_LOBBY, "回到大世界", steps.step_ensure_lobby),
        DailyStep(STEP_COMMISSIONS, "委托领奖", steps.step_claim_commissions),
        DailyStep(STEP_RESIN_SWEEP, "树脂本扫荡", steps.step_resin_domain_sweep),
        DailyStep(STEP_EXPEDITIONS, "探索派遣", steps.step_claim_expeditions),
        DailyStep(STEP_TEAPOT, "尘歌壶领取", steps.step_claim_teapot),
    ],
)

STEP_LABELS: dict[str, str] = {step.step_id: step.name for step in GENSHIN_DAILY_FLOW.steps}
