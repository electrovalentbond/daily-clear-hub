from __future__ import annotations

from games.bhxy2 import features as F
from games.flow import FlowContext, StepOutcome


def _close_popups(ctx: FlowContext, rounds: int = 4) -> None:
    for _ in range(rounds):
        if not ctx.find_feature(F.BH2_CLOSE_POPUP):
            break
        ctx.click_feature(F.BH2_CLOSE_POPUP, timeout=2)


def step_ensure_home(ctx: FlowContext) -> StepOutcome:
    _close_popups(ctx)
    if ctx.find_feature(F.BH2_HOME):
        return StepOutcome.SUCCESS
    if ctx.click_ocr(["主页", "Home", "返回"]):
        _close_popups(ctx)
        return StepOutcome.SUCCESS
    return StepOutcome.SKIPPED


def step_daily_checkin(ctx: FlowContext) -> StepOutcome:
    """每日签到。"""
    if not ctx.click_feature(F.BH2_CHECKIN):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_ocr(["签到", "领取", "确认"])
    ctx.click_feature(F.BH2_OK, timeout=2)
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_adventure(ctx: FlowContext) -> StepOutcome:
    """冒险关卡领取/扫荡（MVP 导航）。"""
    if not ctx.click_feature(F.BH2_ADVENTURE_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.2)
    ok = ctx.click_feature(F.BH2_ADVENTURE_CLAIM)
    if not ok:
        ok = ctx.click_ocr(["扫荡", "领取", "挑战", "确认"])
    ctx.click_feature(F.BH2_OK, timeout=2)
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_shop_freebies(ctx: FlowContext) -> StepOutcome:
    """商店免费礼包/每日购买。"""
    if not ctx.click_feature(F.BH2_SHOP_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_feature(F.BH2_SHOP_FREE)
    if not ok:
        ok = ctx.click_ocr(["免费", "领取", "购买"])
    ctx.click_feature(F.BH2_OK, timeout=2)
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_claim_mail(ctx: FlowContext) -> StepOutcome:
    if not ctx.click_feature(F.BH2_MAIL_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_feature(F.BH2_MAIL_CLAIM)
    if not ok:
        ok = ctx.click_ocr(["全部领取", "领取"])
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED


def step_claim_event(ctx: FlowContext) -> StepOutcome:
    """活动页奖励领取（可选，活动常变）。"""
    if not ctx.click_feature(F.BH2_EVENT_ENTRY):
        return StepOutcome.SKIPPED
    ctx.sleep(1.0)
    ok = ctx.click_feature(F.BH2_EVENT_CLAIM)
    if not ok:
        ok = ctx.click_ocr(["领取", "一键领取"])
    ctx.click_ocr(["返回", "Back"])
    return StepOutcome.SUCCESS if ok else StepOutcome.SKIPPED
