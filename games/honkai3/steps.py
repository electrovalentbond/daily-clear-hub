from __future__ import annotations

from games.flow import FlowContext, StepOutcome
from games.honkai3 import features as F


def _close_popups(ctx: FlowContext, rounds: int = 3) -> None:
    for _ in range(rounds):
        if not ctx.find_feature(F.BH3_CLOSE_POPUP):
            break
        ctx.click_feature(F.BH3_CLOSE_POPUP, timeout=2)


def step_ensure_lobby(ctx: FlowContext) -> StepOutcome:
    """回到舰桥主界面并关闭弹窗。"""
    _close_popups(ctx)
    if ctx.find_feature(F.BH3_MAIN_MENU):
        return StepOutcome.SUCCESS
    if ctx.click_ocr(["返回", "Back", "舰桥"]):
        _close_popups(ctx)
        return StepOutcome.SUCCESS
    return StepOutcome.SKIPPED


def step_material_expedition(ctx: FlowContext) -> StepOutcome:
    """材料远征：打开远征界面并尝试一键派遣/领取。"""
    if not ctx.click_feature(F.BH3_EXPEDITION_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    dispatched = ctx.click_feature(F.BH3_EXPEDITION_DISPATCH)
    claimed = ctx.click_feature(F.BH3_EXPEDITION_CLAIM)
    ctx.click_ocr(["返回", "Back"])
    if dispatched or claimed:
        return StepOutcome.SUCCESS
    return StepOutcome.SKIPPED


def step_homeworld_gold(ctx: FlowContext) -> StepOutcome:
    """家园金币领取。"""
    if not ctx.click_feature(F.BH3_HOMEWORLD_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_feature(F.BH3_HOMEWORLD_GOLD)
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_homeworld_work(ctx: FlowContext) -> StepOutcome:
    """家园打工派遣。"""
    if not ctx.click_feature(F.BH3_HOMEWORLD_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_feature(F.BH3_HOMEWORLD_WORK)
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_homeworld_expedition(ctx: FlowContext) -> StepOutcome:
    """家园远征派遣。"""
    if not ctx.click_feature(F.BH3_HOMEWORLD_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_feature(F.BH3_HOMEWORLD_EXPEDITION)
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_armada_commission(ctx: FlowContext) -> StepOutcome:
    """舰团每日委托。"""
    if not ctx.click_feature(F.BH3_ARMADA_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_feature(F.BH3_ARMADA_COMMISSION)
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_claim_daily_rewards(ctx: FlowContext) -> StepOutcome:
    """领取日常任务奖励。"""
    if not ctx.click_feature(F.BH3_MISSIONS_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_feature(F.BH3_DAILY_REWARD)
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_claim_credential_rewards(ctx: FlowContext) -> StepOutcome:
    """领取凭证（通行证）任务奖励。"""
    if not ctx.click_feature(F.BH3_MISSIONS_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_feature(F.BH3_CREDENTIAL_REWARD)
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_claim_mail(ctx: FlowContext) -> StepOutcome:
    """领取邮件奖励。"""
    if not ctx.click_feature(F.BH3_MAIL_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_feature(F.BH3_MAIL_CLAIM_ALL)
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_sim_battle_reduce(ctx: FlowContext) -> StepOutcome:
    """模拟作战室减负（MVP：仅导航并尝试减负入口）。"""
    if not ctx.click_feature(F.BH3_SIM_BATTLE_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_feature(F.BH3_SIM_BATTLE_REDUCE)
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED
