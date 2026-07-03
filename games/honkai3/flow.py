from __future__ import annotations

from games.flow import DailyFlow, DailyStep
from games.honkai3 import steps

# 步骤 ID 与 config 开关键一致
STEP_ENSURE_LOBBY = "bh3_ensure_lobby"
STEP_MATERIAL_EXPEDITION = "bh3_material_expedition"
STEP_HOMEWORLD_GOLD = "bh3_homeworld_gold"
STEP_HOMEWORLD_WORK = "bh3_homeworld_work"
STEP_HOMEWORLD_EXPEDITION = "bh3_homeworld_expedition"
STEP_ARMADA_COMMISSION = "bh3_armada_commission"
STEP_CLAIM_DAILY = "bh3_claim_daily"
STEP_CLAIM_CREDENTIAL = "bh3_claim_credential"
STEP_CLAIM_MAIL = "bh3_claim_mail"
STEP_SIM_BATTLE_REDUCE = "bh3_sim_battle_reduce"

DEFAULT_STEP_TOGGLES: dict[str, bool] = {
    STEP_ENSURE_LOBBY: True,
    STEP_MATERIAL_EXPEDITION: True,
    STEP_HOMEWORLD_GOLD: True,
    STEP_HOMEWORLD_WORK: True,
    STEP_HOMEWORLD_EXPEDITION: True,
    STEP_ARMADA_COMMISSION: True,
    STEP_CLAIM_DAILY: True,
    STEP_CLAIM_CREDENTIAL: True,
    STEP_CLAIM_MAIL: True,
    STEP_SIM_BATTLE_REDUCE: False,
}

HONKAI3_DAILY_FLOW = DailyFlow(
    game_id="honkai3",
    steps=[
        DailyStep(STEP_ENSURE_LOBBY, "回到舰桥", steps.step_ensure_lobby),
        DailyStep(STEP_MATERIAL_EXPEDITION, "材料远征", steps.step_material_expedition),
        DailyStep(STEP_HOMEWORLD_GOLD, "家园金币", steps.step_homeworld_gold),
        DailyStep(STEP_HOMEWORLD_WORK, "家园打工", steps.step_homeworld_work),
        DailyStep(STEP_HOMEWORLD_EXPEDITION, "家园远征", steps.step_homeworld_expedition),
        DailyStep(STEP_ARMADA_COMMISSION, "舰团每日委托", steps.step_armada_commission),
        DailyStep(STEP_CLAIM_DAILY, "日常任务奖励", steps.step_claim_daily_rewards),
        DailyStep(STEP_CLAIM_CREDENTIAL, "凭证任务奖励", steps.step_claim_credential_rewards),
        DailyStep(STEP_CLAIM_MAIL, "邮件领取", steps.step_claim_mail),
        DailyStep(STEP_SIM_BATTLE_REDUCE, "模拟作战室减负", steps.step_sim_battle_reduce),
    ],
)

STEP_LABELS: dict[str, str] = {step.step_id: step.name for step in HONKAI3_DAILY_FLOW.steps}
