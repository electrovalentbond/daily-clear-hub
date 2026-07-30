from __future__ import annotations

from games.flow import FlowContext, StepOutcome
from games.genshin import features as F


def _close_popups(ctx: FlowContext, rounds: int = 3) -> None:
    for _ in range(rounds):
        if not ctx.find_feature(F.GI_CLOSE_POPUP):
            break
        ctx.click_feature(F.GI_CLOSE_POPUP, timeout=2)


def step_ensure_lobby(ctx: FlowContext) -> StepOutcome:
    _close_popups(ctx)
    if ctx.find_feature(F.GI_LOBBY):
        return StepOutcome.SUCCESS
    if ctx.click_ocr(["返回", "Esc", "Back"]):
        _close_popups(ctx)
        return StepOutcome.SUCCESS
    return StepOutcome.SKIPPED


def step_claim_commissions(ctx: FlowContext) -> StepOutcome:
    """委托领奖（需已完成或减负后领取）。"""
    if not ctx.click_feature(F.GI_QUEST_BOOK):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_feature(F.GI_COMMISSION_CLAIM)
    if not ok:
        ok = ctx.click_ocr(["领取", "每日委托", "Claim"])
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_resin_domain_sweep(ctx: FlowContext) -> StepOutcome:
    """树脂本扫荡（圣遗物/天赋本等简化为扫荡入口）。"""
    if not ctx.click_feature(F.GI_DOMAIN_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.2)
    ok = ctx.click_feature(F.GI_RESIN_SWEEP)
    if ok:
        ctx.click_ocr(["浓缩树脂", "树脂", "确认", "开始挑战"])
        ctx.click_feature(F.GI_OK, timeout=2)
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_claim_expeditions(ctx: FlowContext) -> StepOutcome:
    """探索派遣领取。"""
    if not ctx.click_feature(F.GI_EXPEDITION_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_feature(F.GI_EXPEDITION_CLAIM)
    if not ok:
        ok = ctx.click_ocr(["领取", "再次派遣", "Claim"])
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_claim_teapot(ctx: FlowContext) -> StepOutcome:
    """尘歌壶货币/信任等领取（可选）。"""
    if not ctx.click_feature(F.GI_TEAPOT_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.5)
    ok = ctx.click_feature(F.GI_TEAPOT_CLAIM)
    if not ok:
        ok = ctx.click_ocr(["好友互动", "领取", "信任等阶"])
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED
