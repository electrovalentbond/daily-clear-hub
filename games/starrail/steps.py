from __future__ import annotations

from games.flow import FlowContext, StepOutcome
from games.starrail import features as F


def _close_popups(ctx: FlowContext, rounds: int = 3) -> None:
    for _ in range(rounds):
        if not ctx.find_feature(F.SR_CLOSE_POPUP):
            break
        ctx.click_feature(F.SR_CLOSE_POPUP, timeout=2)


def step_ensure_lobby(ctx: FlowContext) -> StepOutcome:
    """回到大世界/手机可用状态。"""
    _close_popups(ctx)
    if ctx.find_feature(F.SR_PHONE):
        return StepOutcome.SUCCESS
    if ctx.click_ocr(["返回", "Esc", "Back"]):
        _close_popups(ctx)
        return StepOutcome.SUCCESS
    return StepOutcome.SKIPPED


def step_claim_assignments(ctx: FlowContext) -> StepOutcome:
    """委托领取与重新派遣。"""
    if not ctx.click_feature(F.SR_ASSIGNMENT_ENTRY):
        if not ctx.click_feature(F.SR_PHONE):
            return StepOutcome.SKIPPED
        ctx.sleep(0.8)
        if not ctx.click_feature(F.SR_ASSIGNMENT_ENTRY):
            return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    claimed = ctx.click_feature(F.SR_ASSIGNMENT_CLAIM)
    dispatched = ctx.click_feature(F.SR_ASSIGNMENT_DISPATCH)
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if claimed or dispatched else StepOutcome.SKIPPED


def step_spend_trailblaze_power(ctx: FlowContext) -> StepOutcome:
    """消耗开拓力：进入拟造花萼并尝试扫荡。"""
    if not ctx.click_feature(F.SR_CALYX_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.2)
    ok = ctx.click_feature(F.SR_SWEEP_BUTTON)
    if ok:
        ctx.click_ocr(["确认", "开始", "挑战", "OK"])
        ctx.click_feature(F.SR_OK, timeout=2)
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_claim_daily_training(ctx: FlowContext) -> StepOutcome:
    """领取每日实训奖励。"""
    if not ctx.click_feature(F.SR_DAILY_TRAINING):
        if not ctx.click_feature(F.SR_PHONE):
            return StepOutcome.SKIPPED
        ctx.sleep(0.8)
        if not ctx.click_feature(F.SR_DAILY_TRAINING):
            return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_feature(F.SR_DAILY_CLAIM)
    if not ok:
        ok = ctx.click_ocr(["领取", "一键领取", "Claim"])
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_claim_mail(ctx: FlowContext) -> StepOutcome:
    """领取邮件。"""
    if not ctx.click_feature(F.SR_MAIL_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_feature(F.SR_MAIL_CLAIM)
    if not ok:
        ok = ctx.click_ocr(["全部领取", "领取", "Claim"])
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED
