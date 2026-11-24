"""Sweep already cleared hard stages in the currently open revival."""

from __future__ import annotations

import re

from pcrscript.game_ui.event_layout import event_layout
from pcrscript.game_ui.screen import EventUIError, normalized
from pcrscript.run_session import clock as time
from pcrscript.tasks import BaseTask
from pcrscript.tasks.event_sweep import HardSweep
from pcrscript.tasks.revival_map import RevivalMap
from pcrscript.tasks.task_home import ToHomePage
from pcrscript.tasks.task_revival_event import RevivalEventOnce
from pcrscript.templates import ImageTemplate


MAP_LABELS = (0, 135, 960, 465)
DETAIL_TITLE = (40, 23, 560, 81)
ATTEMPTS = (850, 388, 945, 445)
TICKETS = (830, 263, 925, 304)
STAMINA_BEFORE = (635, 387, 699, 444)
STAMINA_AFTER = (707, 387, 767, 444)
SWEEP_BUTTON = (675, 311, 828, 390)
CONFIRM_TITLE = (270, 106, 690, 183)
CONFIRM_BODY = (230, 180, 730, 328)
CONFIRM_BUTTON = (480, 334, 730, 407)
UNSAFE_PROMPT = r"购买体力|体力回[复復]|体力恢复|恢复挑战次数|剩余挑战次数恢复|消耗宝石|扫荡券不足"
LOCKED_SWEEP = r"未达(?:成|到)\s*3星|(?:3|三)星(?:评价)?通关后|(?:3|三)星(?:评价)?通关才|(?:3|三)星(?:评价)?通关可"
LOCKED_STAGE = r"关卡尚未解锁|关卡未解锁|关卡尚未开放|通关(?:前|上一)(?:一?个)?关卡后"


def enter_active_revival(robot):
    """Reuse upstream navigation without touching its once-per-event state."""
    news = getattr(robot, "_event_news", None)
    if news is None:
        from pcrscript.news import fetch_event_news

        news = fetch_event_news()
    event = news.revival
    if event is None or not event.startTimestamp <= time.time() < event.endTimestamp:
        return None
    options = {"collect_house_stamina": False}
    if output := getattr(robot, "_task_output", None):
        options["output"] = str(output)
    runner = RevivalEventOnce(robot, options=options)
    runner.event = event
    runner.report.update(event=event.name, event_id=event.extras["event_id"])
    runner.enter()
    return runner


def stage_title(screen, name):
    return screen.find(rf"(?:活动关卡|关卡)?{re.escape(name)}(?:\D.*)?", DETAIL_TITLE, exact=True)


def sweep_count(screen):
    button = screen.find(r"(?:使用|消耗)[1-3]张(?:扫荡券)?", SWEEP_BUTTON, exact=True)
    if button and screen.blue_button(button):
        return button, int(re.search(r"[1-3]", normalized(button.text))[0])
    return None, None


class MapHardSweep:
    def __init__(self, runner):
        self.runner = runner
        self.map = RevivalMap(runner)
        self.ui = runner.ui
        self.hard_selected = ImageTemplate("btn_hard_selected", threshold=.90, roi=(810, 45, 960, 115))

    def on_hard_tab(self, screen):
        if self.hard_selected.match(screen.image):
            return True
        label = screen.find("困难", (810, 50, 960, 115), exact=True)
        if label is None or label.score < .90:
            return False
        x, y = label.center
        # The selected legacy tab has a red fill and the unselected one is white.
        patch = screen.image[y-10:y+11, max(0, x-27):x+28].astype("int16")
        blue, green, red = patch.transpose(2, 0, 1)
        return bool(((red > 155) & (red - green > 50) & (red - blue > 45)).mean() > .28)

    def open_hard(self):
        screen = self.map.home()
        if not self.on_hard_tab(screen):
            self.ui.expect_click("困难", (810, 50, 960, 115), exact=True)
        return self.ui.wait(
            lambda frame: self.on_hard_tab(frame)
            and frame.find("讨伐证交换", (700, 360, 960, 480)),
            "确认复刻困难地图",
            timeout=12,
        )

    def stage(self, name):
        screen = self.open_hard()
        pattern = re.escape(name)
        # Most legacy maps expose all five hard nodes at once. Check both
        # directions when a prior task or an event animation shifted the map.
        for shift in (1, -1, -1, 0):
            label = (screen.find(pattern, MAP_LABELS, exact=True)
                     or self.ui.read_region(screen, MAP_LABELS).find(pattern, MAP_LABELS, exact=True))
            if label:
                self.ui.click((label.center[0], label.center[1] - 55))
                detail = self.ui.wait(
                    lambda frame: (
                        stage_title(frame, name)
                        and (frame.find("剩余挑战次数", (760, 355, 955, 447))
                             or frame.find(LOCKED_SWEEP, (550, 244, 948, 401)))
                    )
                    or frame.find(LOCKED_STAGE, (240, 130, 720, 355)),
                    f"确认复刻困难 {name} 详情",
                    timeout=12,
                )
                if detail.find(LOCKED_STAGE, (240, 130, 720, 355)):
                    close = detail.find("取消|关闭", (250, 330, 710, 482), exact=True)
                    if close is None and not detail.find(UNSAFE_PROMPT, (200, 85, 800, 525)):
                        close = detail.find("确认|确定|OK", (250, 330, 710, 482), exact=True)
                    if close is None:
                        raise EventUIError(f"无法关闭复刻困难 {name} 的锁定提示")
                    self.ui.click(close)
                    self.skip(name, "关卡尚未开放")
                    return None
                return detail
            if shift:
                start, end = ((230, 258), (730, 258)) if shift > 0 else ((730, 258), (230, 258))
                self.ui.swipe(start, end)
                screen = self.open_hard()
        raise EventUIError(f"复刻困难地图未定位到 {name}")

    def remaining(self, screen, name):
        if not stage_title(screen, name):
            return None
        pattern = r"(?:剩余挑战次数)?([0-3])/3"
        item = screen.find(pattern, ATTEMPTS, exact=True)
        if item is None:
            item = self.ui.read_region(screen, ATTEMPTS).find(pattern, ATTEMPTS, exact=True)
        return int(re.fullmatch(pattern, normalized(item.text))[1]) if item else None

    def sweep_stage(self, screen, name):
        if stage_title(screen, name) and screen.find(LOCKED_SWEEP, (550, 244, 948, 401)):
            return self.skip(name, "未达到扫荡解锁条件")
        remaining = self.remaining(screen, name)
        if remaining is None:
            raise EventUIError(f"无法核对复刻困难 {name} 的剩余次数")
        if remaining == 0:
            return 0
        stock_label = screen.find(r"\d{1,3}(?:,\d{3})+", TICKETS, exact=True)
        stock = int(normalized(stock_label.text).replace(",", "")) if stock_label else self.ui.number(screen, TICKETS)
        stamina = self.ui.number(screen, STAMINA_BEFORE)
        if stock is None or stamina is None:
            raise EventUIError(f"无法读取复刻困难 {name} 的体力或扫荡券")
        if stock == 0 or stamina < 10 or screen.find("体力不足|扫荡券不足", (550, 244, 948, 440)):
            return self.skip(name, "现有体力或扫荡券不足")
        button, current = sweep_count(screen)
        if button is None:
            raise EventUIError(f"未核实复刻困难 {name} 的可用扫荡按钮")
        after = self.ui.number(screen, STAMINA_AFTER)
        if after is None:
            raise EventUIError(f"无法读取复刻困难 {name} 的体力预览")
        cost, remainder = divmod(stamina - after, current)
        if remainder or cost not in (10, 20):
            raise EventUIError(f"复刻困难 {name} 的体力预览与扫荡次数不符")
        target = min(remaining, stock, stamina // cost)
        if not target:
            return self.skip(name, "现有体力或扫荡券不足")
        for _ in range(4):
            if current == target:
                break
            self.ui.click((878 if current < target else 626, button.center[1]), delay=.4)
            screen = self.ui.capture()
            button, current = sweep_count(screen)
            if button is None or self.remaining(screen, name) != remaining:
                raise EventUIError(f"调整复刻困难 {name} 的扫荡次数后界面发生变化")
        else:
            raise EventUIError(f"无法调整复刻困难 {name} 的扫荡次数")
        before = self.ui.number(screen, STAMINA_BEFORE)
        after = self.ui.number(screen, STAMINA_AFTER)
        if before is None or after is None or before - after != target * cost:
            raise EventUIError(f"复刻困难 {name} 的体力预览与扫荡次数不符")
        self.ui.save(f"revival_hard_{name}_plan", screen)
        self.ui.click(button)
        self.settle(name, remaining - target)
        if target < remaining:
            self.skip(name, f"现有体力或扫荡券不足，剩余 {remaining - target} 次")
        return target

    def skip(self, name, reason):
        self.runner.report.setdefault("sweep_skipped", {})[name] = reason
        self.runner.log(f"跳过复刻困难 {name}：{reason}")
        return 0

    def settle(self, name, expected_remaining):
        submitted = False
        saw_receipt = False
        for _ in range(40):
            self.runner.check_deadline()
            screen = self.ui.capture()
            if screen.find(UNSAFE_PROMPT, (200, 85, 800, 525)):
                cancel = screen.find("取消|关闭", (200, 300, 800, 520), exact=True)
                if cancel:
                    self.ui.click(cancel)
                raise EventUIError("扫荡遇到资源或次数恢复提示，停止消费")
            if screen.find("扫荡券确认", CONFIRM_TITLE, exact=True):
                if not submitted:
                    prompt = normalized(screen.text(CONFIRM_BODY))
                    if not all(word in prompt for word in ("扫荡券", "体力", "关卡")):
                        raise EventUIError("复刻困难扫荡确认与体力、扫荡券计划不符")
                    button = screen.find("确认|确定|OK", CONFIRM_BUTTON, exact=True)
                    if button and screen.blue_button(button):
                        self.ui.save(f"revival_hard_{name}_confirm", screen)
                        self.ui.click(button)
                        submitted = True
            elif submitted and screen.find(
                "扫荡结果|扫荡券使用结果|扫荡完成", (240, 0, 720, 90), exact=True
            ):
                saw_receipt = True
                button = screen.find("跳过完毕|全部跳过|跳过|确认|确定|关闭|OK", (200, 410, 850, 535), exact=True)
                if button:
                    self.ui.click(button)
            elif submitted and screen.find("限定商店|限时商店", (200, 115, 800, 320)):
                self.ui.expect_click("取消|关闭", (200, 300, 800, 525), exact=True)
            elif submitted and not screen.find("正在.*连接|加载中|下载中"):
                if saw_receipt and event_layout(screen) == "map" and not stage_title(screen, name):
                    screen = self.stage(name)
                    if screen is None:
                        raise EventUIError(f"无法返回复刻困难 {name} 核对扫荡结果")
                if self.remaining(screen, name) == expected_remaining:
                    self.ui.save(f"revival_hard_{name}_settled", screen)
                    return
            time.sleep(.55)
        raise EventUIError(f"未核实复刻困难 {name} 扫荡后的剩余次数")

    def run(self):
        counts = {}
        self.runner.report["sweep_counts"] = counts
        for number in range(1, 6):
            name = f"1-{number}"
            self.runner.report_progress(f"复刻困难 {name}", number - 1, 5)
            screen = self.stage(name)
            if screen is None:
                counts[name] = 0
                continue
            counts[name] = self.sweep_stage(screen, name)
            self.ui.expect_click("取消", (550, 420, 755, 525), exact=True)
        return any(counts.values())


class SweepRevivalHard(BaseTask):
    def run(self):
        self.report_progress("检查复刻开放时间")
        runner = enter_active_revival(self.robot)
        if runner is None:
            return {"status": "unavailable", "reason": "当前没有开放挑战的复刻活动"}
        if runner.layout == "list":
            self.report_progress("扫荡列表式复刻困难关卡")
            already_complete = HardSweep(runner).run() is True
        else:
            already_complete = not MapHardSweep(runner).run()
        report = runner.report
        if (skipped := report.get("sweep_skipped")):
            done = sum(report["sweep_counts"].values())
            report["status"] = "unavailable"
            report["reason"] = f"已扫荡 {done} 次；" + "；".join(f"{name} {why}" for name, why in skipped.items())
        elif report["pending"] and all("体力不足以完成困难批量扫荡" in reason for reason in report["pending"]):
            report["status"] = "unavailable"
        elif report["pending"]:
            report["status"] = "partial"
            return report
        else:
            report["status"] = "already_complete" if already_complete else "complete"
        ToHomePage(self.robot).run(timeout=60)
        return report
