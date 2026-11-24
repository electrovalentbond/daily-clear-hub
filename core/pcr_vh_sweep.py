"""Sweep one unlocked Very Hard boss in an active legacy-map revival."""

from __future__ import annotations

from pcrscript.game_ui.event_layout import legacy_hub
from pcrscript.game_ui.screen import EventUIError, normalized
from pcrscript.tasks import BaseTask
from pcrscript.tasks.revival_map import RevivalMap

from core.pcr_revival_sweep import enter_active_revival


VH = r"高难(?:度)?|非常困难|VERYHARD"
SWEEP_ONE = r"击败1只|使用1张(?:扫荡券)?"
SWEEP_CONFIRMATION = r"扫荡券确认|扫荡确认"
SWEEP_RESULT = r"扫荡结果|扫荡券使用结果|扫荡完成"
# The legacy CN client spends 30 boss tickets for one Very Hard sweep.
BOSS_TICKET_COST = 30
VH_BADGE = (170, 22, 425, 72)
BOSS_PANE = (675, 135, 940, 307)
TICKET_BEFORE = (831, 412, 875, 439)
TICKET_AFTER = (884, 412, 928, 439)
SWEEP_TICKETS = (795, 318, 855, 345)


def high_confidence(screen, pattern, region):
    item = screen.find(pattern, region, exact=True)
    return item if item is not None and item.score >= .90 else None


def remaining_today(screen):
    """Only a daily counter can show completion, not lifetime boss defeats."""
    region = (635, 15, 949, 494)
    if high_confidence(screen, r"今日已(?:讨伐|击败)|(?:当日|今日)(?:挑战|扫荡)次数已用完", region):
        return 0
    label = r"(?:今日)?剩余(?:挑战|扫荡|讨伐)次数"
    counter = high_confidence(screen, label + r"[:：]?[01]/1", region)
    if counter is not None:
        return int(normalized(counter.text)[-3])
    anchor = high_confidence(screen, label + r"[:：]?", region)
    if anchor is not None:
        x, y = anchor.center
        row = high_confidence(screen, r"[01]/1", (x + 35, y - 12, 949, y + 12))
        if row is not None:
            return int(normalized(row.text)[0])
    return None


def sweep_preview(ui, screen):
    """Verify ticket counts for a single submission from the legacy boss panel."""
    # The full-frame recognizer can merge balances on both sides of the arrow
    # into a single high-confidence string such as 5525 for 55 → 25.
    return tuple(ui.number(ui.read_region(screen, region, classify=False), region)
                 for region in (TICKET_BEFORE, TICKET_AFTER, SWEEP_TICKETS))


def confirmation(screen):
    return high_confidence(screen, SWEEP_CONFIRMATION, (275, 104, 690, 207))


def result(screen):
    return high_confidence(screen, SWEEP_RESULT, (265, 14, 700, 155))


def boss_detail(screen):
    return high_confidence(screen, r"(?:BOSS|首领)详情", (15, 10, 310, 80))


def result_button(screen):
    return high_confidence(screen, r"全部跳过|跳过完毕|跳过|确认|关闭|下一步|OK", (375, 400, 945, 530))


def close_detail(ui, screen):
    cancel = high_confidence(screen, "取消", (550, 425, 775, 510))
    if not cancel:
        raise EventUIError("首领详情关闭按钮无法识别")
    ui.click(cancel)
    ui.wait(legacy_hub, "返回复刻首领列表", timeout=8)


class SweepVeryHardBoss(BaseTask):
    def open_vh(self, runner):
        ui = runner.ui
        screen = RevivalMap(runner).hub()
        # The old hub contains its own vertical list of bosses. Keep the drag
        # inside it so it can never land on an event-stage or exchange button.
        for i in range(4):
            if not legacy_hub(screen):
                raise EventUIError("未核实复刻活动首领列表")
            if name := high_confidence(screen, VH, BOSS_PANE):
                x, y = name.center
                if cost := high_confidence(screen, r"[1-9]\d{0,2}张来挑战", (x + 45, y - 14, 935, y + 14)):
                    if int(normalized(cost.text).split("张")[0]) != BOSS_TICKET_COST:
                        raise EventUIError("高难首领列表的挑战券消耗与旧版扫荡规则不符")
                ui.click(name)
                return self.wait_detail(ui)
            if i < 3:
                ui.swipe((820, 285), (820, 145), duration=400)
                screen = ui.capture()
        return None

    @staticmethod
    def wait_detail(ui):
        screen = ui.wait(boss_detail, "打开复刻高难首领详情", timeout=12)
        badge = high_confidence(screen, VH, VH_BADGE)
        if not badge:
            badge = high_confidence(ui.read_region(screen, VH_BADGE), VH, VH_BADGE)
        if not badge:
            raise EventUIError("首领详情未确认高难（VH）标签")
        return screen

    @staticmethod
    def settle(ui):
        screen = ui.wait(lambda frame: result(frame) or (
            boss_detail(frame) and high_confidence(frame, VH, VH_BADGE) and remaining_today(frame) == 0
        ), "核对高难首领扫荡结果", timeout=30)
        ui.save("vh_sweep_result", screen)
        # Result animation controls only apply while its title remains on
        # screen. Never tap the underlying boss panel a second time.
        for _ in range(3):
            if not result(screen):
                break
            screen = ui.wait(lambda frame: not result(frame) or result_button(frame), "识别高难扫荡回执按钮", timeout=8)
            if result(screen):
                ui.click(result_button(screen))
                screen = ui.capture()
        screen = ui.wait(lambda frame: not result(frame) and (legacy_hub(frame) or boss_detail(frame)),
                         "收起高难扫荡回执", timeout=10)
        if boss_detail(screen):
            close_detail(ui, screen)

    def run(self):
        self.report_progress("进入当前复刻活动")
        runner = enter_active_revival(self.robot)
        if runner is None:
            return {"status": "unavailable", "reason": "当前没有可进入的复刻活动"}
        ui = runner.ui
        if runner.layout != "map":
            return {"status": "unavailable", "reason": "当前活动不是带首领挑战券的旧版复刻地图"}

        self.report_progress("核对高难首领扫荡条件")
        try:
            screen = self.open_vh(runner)
            if screen is None:
                return {"status": "unavailable", "reason": "本期列表未发现高难首领"}
            if remaining_today(screen) == 0:
                close_detail(ui, screen)
                return {"status": "already_complete"}
            button = high_confidence(screen, SWEEP_ONE, (700, 330, 820, 412))
            if button is None or not screen.blue_button(button):
                close_detail(ui, screen)
                return {"status": "unavailable", "reason": "高难首领今日无可用扫荡或尚未解锁扫荡"}
            if not high_confidence(screen, r"首领挑战券数量|BOSS券数量", (580, 395, 810, 450)):
                raise EventUIError("未核实首领挑战券余额行")
            before, after, tickets = sweep_preview(ui, screen)
            if (before is not None and before < BOSS_TICKET_COST) or tickets == 0:
                close_detail(ui, screen)
                return {"status": "unavailable", "reason": "现有首领挑战券或扫荡券不足"}
            if before is None or after is None or tickets is None or before - after != BOSS_TICKET_COST:
                raise EventUIError("无法核对高难首领一次扫荡所需的 30 张挑战券及扫荡券余额")
            ui.save("vh_sweep_plan", screen)
            ui.click(button)
            preview = ui.wait(confirmation, "核对高难首领扫荡确认", timeout=12)
            confirm = high_confidence(preview, r"确认|确定|OK", (495, 314, 708, 436))
            cancel = high_confidence(preview, r"取消", (260, 314, 477, 436))
            if not cancel or not confirm or not preview.blue_button(confirm):
                raise EventUIError("扫荡确认按钮未核实，未提交扫荡")
            if preview.find(r"宝石|回复次数|恢复次数|购买|(?:扫荡|击败)(?:[2-9]|\d{2,})[次只]|(?:[2-9]|\d{2,})次扫荡",
                            (240, 140, 720, 440)):
                ui.click(cancel)
                raise EventUIError("确认内容超出一次高难扫荡范围，已取消")
            ui.save("vh_sweep_confirmation", preview)
            ui.click(confirm)
            self.settle(ui)
            return {"status": "complete", "swept": 1}
        except EventUIError as error:
            ui.save("vh_sweep_blocked")
            return {"status": "blocked", "reason": str(error)}
