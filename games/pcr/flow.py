from __future__ import annotations

from games.flow import DailyFlow, DailyStep
from games.pcr import steps

STEP_ENSURE_HOME = "pcr_ensure_home"
STEP_COLLECT_GIFTS = "pcr_collect_gifts"
STEP_COLLECT_QUESTS = "pcr_collect_quests"
STEP_SWEEP = "pcr_sweep"
STEP_DUNGEON_SUPPORT = "pcr_dungeon_support"
STEP_GUILD_DONATE = "pcr_guild_donate"

DEFAULT_STEP_TOGGLES: dict[str, bool] = {
    STEP_ENSURE_HOME: True,
    STEP_COLLECT_GIFTS: True,
    STEP_COLLECT_QUESTS: True,
    STEP_SWEEP: True,
    STEP_DUNGEON_SUPPORT: True,
    STEP_GUILD_DONATE: True,
}

PCR_DAILY_FLOW = DailyFlow(
    game_id="pcr",
    steps=[
        DailyStep(STEP_ENSURE_HOME, "回到主界面", steps.step_ensure_home),
        DailyStep(STEP_COLLECT_GIFTS, "收取礼物", steps.step_collect_gifts),
        DailyStep(STEP_COLLECT_QUESTS, "收取任务", steps.step_collect_quests),
        DailyStep(STEP_SWEEP, "扫荡关卡", steps.step_sweep_stages),
        DailyStep(STEP_DUNGEON_SUPPORT, "地下城借支援", steps.step_dungeon_support),
        DailyStep(STEP_GUILD_DONATE, "行会捐赠", steps.step_guild_donate),
    ],
)

STEP_LABELS: dict[str, str] = {step.step_id: step.name for step in PCR_DAILY_FLOW.steps}
