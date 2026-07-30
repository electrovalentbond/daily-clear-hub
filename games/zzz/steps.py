from __future__ import annotations

from games.flow import FlowContext, StepOutcome
from games.zzz import features as F


def _close_popups(ctx: FlowContext, rounds: int = 3) -> None:
    for _ in range(rounds):
        if not ctx.find_feature(F.ZZZ_CLOSE_POPUP):
            break
        ctx.click_feature(F.ZZZ_CLOSE_POPUP, timeout=2)


def step_ensure_lobby(ctx: FlowContext) -> StepOutcome:
    _close_popups(ctx)
    if ctx.find_feature(F.ZZZ_LOBBY):
        return StepOutcome.SUCCESS
    if ctx.click_ocr(["返回", "Back", "Esc"]):
        _close_popups(ctx)
        return StepOutcome.SUCCESS
    return StepOutcome.SKIPPED


def step_business_scratch(ctx: FlowContext) -> StepOutcome:
    """录像店营业 / 刮卡等轻量经营。"""
    if not ctx.click_feature(F.ZZZ_BUSINESS_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    scratched = ctx.click_feature(F.ZZZ_SCRATCH_CARD)
    if not scratched:
        scratched = ctx.click_ocr(["刮卡", "营业", "领取", "确认"])
    ctx.click_feature(F.ZZZ_OK, timeout=2)
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if scratched else StepOutcome.SKIPPED


def step_spend_battery(ctx: FlowContext) -> StepOutcome:
    """消耗电量/体力扫荡。"""
    if not ctx.click_feature(F.ZZZ_BATTERY_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.2)
    ok = ctx.click_feature(F.ZZZ_SWEEP_BUTTON)
    if ok:
        ctx.click_ocr(["确认", "开始", "挑战", "扫荡"])
        ctx.click_feature(F.ZZZ_OK, timeout=2)
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_claim_daily_missions(ctx: FlowContext) -> StepOutcome:
    """领取每日任务奖励。"""
    if not ctx.click_feature(F.ZZZ_MISSIONS_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_feature(F.ZZZ_DAILY_CLAIM)
    if not ok:
        ok = ctx.click_ocr(["领取", "一键领取", "Claim"])
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_claim_mail(ctx: FlowContext) -> StepOutcome:
    if not ctx.click_feature(F.ZZZ_MAIL_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_feature(F.ZZZ_MAIL_CLAIM)
    if not ok:
        ok = ctx.click_ocr(["全部领取", "领取"])
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED
