from __future__ import annotations

from games.flow import FlowContext, StepOutcome
from games.pcr import features as F


def _close_popups(ctx: FlowContext, rounds: int = 3) -> None:
    for _ in range(rounds):
        if not ctx.find_feature(F.PCR_CLOSE_POPUP):
            break
        ctx.click_feature(F.PCR_CLOSE_POPUP, timeout=2)


def step_ensure_home(ctx: FlowContext) -> StepOutcome:
    """确保处于主界面（标题/首页）。"""
    _close_popups(ctx)
    if ctx.find_feature(F.PCR_HOME):
        return StepOutcome.SUCCESS
    if ctx.click_ocr(["主页", "Home", "もどる"]):
        _close_popups(ctx)
        return StepOutcome.SUCCESS
    return StepOutcome.SKIPPED


def step_collect_gifts(ctx: FlowContext) -> StepOutcome:
    """收取礼物。"""
    if not ctx.click_feature(F.PCR_GIFT_BOX):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_ocr(["领取", "受け取る", "全部领取"])
    ctx.click_feature(F.PCR_OK_BUTTON, timeout=2)
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_collect_quests(ctx: FlowContext) -> StepOutcome:
    """收取任务奖励。"""
    if not ctx.click_feature(F.PCR_QUEST_CLAIM):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_ocr(["领取", "受け取る", "一键领取"])
    ctx.click_feature(F.PCR_OK_BUTTON, timeout=2)
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_sweep_stages(ctx: FlowContext) -> StepOutcome:
    """扫荡关卡（MVP：进入冒险并尝试扫荡按钮）。"""
    if not ctx.click_feature(F.PCR_ADVENTURE_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.5)
    ok = ctx.click_feature(F.PCR_SWEEP_BUTTON)
    if ok:
        ctx.click_ocr(["扫荡", "掃討", "确定", "OK"])
        ctx.click_feature(F.PCR_OK_BUTTON, timeout=2)
    ctx.click_ocr(["返回", "Back", "もどる"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_dungeon_support(ctx: FlowContext) -> StepOutcome:
    """地下城借用支援角色后退出（农场号经典流程）。"""
    if not ctx.click_feature(F.PCR_DUNGEON_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.5)
    borrowed = ctx.click_feature(F.PCR_SUPPORT_BORROW)
    if borrowed:
        ctx.click_ocr(["确定", "OK", "借りる"])
        ctx.sleep(2.0)
        ctx.click_ocr(["撤退", "退出", "もどる"])
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if borrowed else StepOutcome.SKIPPED


def step_guild_donate(ctx: FlowContext) -> StepOutcome:
    """行会捐赠请求。"""
    if not ctx.click_feature(F.PCR_GUILD_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_feature(F.PCR_GUILD_DONATE)
    if ok:
        ctx.click_ocr(["捐赠", "寄付", "确定"])
        ctx.click_feature(F.PCR_OK_BUTTON, timeout=2)
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED
