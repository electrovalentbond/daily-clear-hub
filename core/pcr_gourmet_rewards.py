"""Collect unlocked Carnival rewards through the B-server game UI."""

import re

from pcrscript.game_ui.screen import EventUI, EventUIError, normalized
from pcrscript.run_session import clock as time
from pcrscript.tasks import BaseTask


TITLE = (40, 0, 270, 65)
HOME_ENTRY = (455, 388, 850, 478)
ENTRY_LABEL = r"(?:美食)?嘉年华"
MERGED_ENTRY = rf"({ENTRY_LABEL})(?:究极炼成|驾车游|商店|日程表)+"
MAIN_TABS = (720, 65, 950, 134)
TASK_TABS = (325, 110, 715, 178)
CLAIM = (741, 360, 946, 482)
RECEIPT = (210, 15, 750, 210)
RECEIPT_CLOSE = (346, 310, 620, 517)
TASK_SECTIONS = ("每日任务", "每周任务", "挑战任务")
TAB_TEXT = {"每周任务": r"(?:每周|本周)任务", "挑战任务": r"挑战任务(?:限时)?"}
LOADING = r"正在进行数据连接|连接中|加载中"
CLAIM_LABEL = r"全部收取|全部领取|一键收取|一键领取"


def in_home(screen):
    return bool(
        screen.find("我的主页", (25, 491, 238, 540), exact=True)
        and screen.find("公会之家|主菜单", (525, 491, 950, 540), exact=True)
        and screen.find("日程表", (686, 397, 855, 477), exact=True)
        and not screen.find(LOADING)
    )


def carnival(screen):
    return bool(
        screen.find("美食嘉年华", TITLE, exact=True)
        and screen.find("任务", MAIN_TABS, exact=True)
        and screen.find("奖励", MAIN_TABS, exact=True)
        and not screen.find(LOADING)
    )


def selected_tab(screen, name, region):
    label = screen.find(TAB_TEXT.get(name, name), region, exact=True)
    if label is None:
        return False
    x, y = label.center
    # The selected tab has a light cream fill; the unselected tab is tan.
    patch = screen.image[y + 7:y + 11, x - 14:x + 15]
    return bool((patch[:, :, 0] >= 200).mean() > .5)


def home_entry(ui, screen):
    entry = screen.find(ENTRY_LABEL, HOME_ENTRY, exact=True)
    if entry is not None:
        return entry
    merged = screen.find(MERGED_ENTRY, HOME_ENTRY, exact=True)
    if merged is not None:
        text = normalized(merged.text)
        prefix = re.fullmatch(MERGED_ENTRY, text)[1]
        xs, ys = zip(*merged.box)
        left, right = min(xs), max(xs)
        split = round(left + (right - left) * len(prefix) / len(text))
        # Adjacent home labels can be returned as one box. Read just the
        # Carnival label again so the click stays inside its own control.
        crop = (max(0, int(left) - 2), max(0, int(min(ys)) - 3), split + 1, int(max(ys)) + 3)
        entry = ui.read_region(screen, crop).find(ENTRY_LABEL, crop, exact=True)
        if entry is None:
            raise EventUIError("识别到美食嘉年华与相邻入口，无法单独确认嘉年华按钮")
        return entry
    return ui.read_region(screen, HOME_ENTRY).find(ENTRY_LABEL, HOME_ENTRY, exact=True)


class ClaimGourmetRewards(BaseTask):
    def __init__(self, robot):
        super().__init__(robot)
        output = getattr(robot, "_task_output", None) or "cache/daily/gourmet_rewards"
        self.ui = EventUI(robot.driver, output)

    def open_carnival(self):
        screen = self.ui.wait(lambda frame: carnival(frame) or in_home(frame), "确认主页或美食嘉年华", timeout=20)
        if carnival(screen):
            return screen
        for attempt in range(3):
            if in_home(screen):
                entry = home_entry(self.ui, screen)
                if entry is not None:
                    self.ui.click(entry)
                    return self.ui.wait(carnival, "进入美食嘉年华", timeout=20)
            if attempt < 2:
                time.sleep(.5)
                screen = self.ui.capture()
        if not in_home(screen):
            raise EventUIError("检查美食嘉年华入口时无法确认主页已就绪")
        self.ui.save("gourmet_no_entry", screen)
        return None

    def select(self, screen, name, region, page):
        def active(frame):
            return page(frame) and selected_tab(frame, name, region)

        if active(screen):
            return screen
        label = screen.find(TAB_TEXT.get(name, name), region, exact=True)
        if label is None or not page(screen):
            raise EventUIError(f"找不到美食嘉年华「{name}」页签")
        self.ui.click(label)
        return self.ui.wait(active, f"切换到美食嘉年华「{name}」", timeout=12)

    def claim(self, screen, section, active):
        def ready(frame):
            return active(frame) and frame.find(CLAIM_LABEL, CLAIM, exact=True)

        screen = screen if ready(screen) else self.ui.wait(ready, f"读取{section}的全部收取按钮", timeout=12)
        for attempt in range(3):
            button = screen.find(CLAIM_LABEL, CLAIM, exact=True)
            if not screen.blue_button(button):
                return screen, attempt > 0
            self.ui.save(f"gourmet_{section}_before_claim", screen)
            self.ui.click(button)
            settled, close = self.wait_for_claim(section, ready)
            self.ui.save(f"gourmet_{section}_receipt", settled)
            if close is None:
                return settled, True
            self.ui.click(close)
            screen = self.ui.wait(ready, f"返回{section}", timeout=12)
        if screen.blue_button(screen.find(CLAIM_LABEL, CLAIM, exact=True)):
            raise EventUIError(f"{section}连续领取后仍有可领报酬")
        return screen, True

    def wait_for_claim(self, section, ready):
        disabled_since = None
        close = None

        def settled(frame):
            nonlocal close, disabled_since
            if frame.find("持有上限", RECEIPT):
                raise EventUIError(f"{section}奖励遇到持有上限")
            receipt = frame.find("收取报酬|收取奖励|收取完成|获得奖励|获得报酬|领取成功|美食等级提升", RECEIPT, exact=True)
            if receipt and not frame.find(LOADING):
                close = frame.find("关闭|确定|确认|OK", RECEIPT_CLOSE, exact=True)
                return close is not None
            button = ready(frame)
            if not button or frame.blue_button(button):
                disabled_since = None
                return False
            now = time.monotonic()
            if disabled_since is None:
                disabled_since = now
            return now - disabled_since >= 1.5

        screen = self.ui.wait(settled, f"核对{section}领奖结果", timeout=20)
        return screen, close

    def run(self):
        self.report_progress("寻找美食嘉年华入口")
        screen = self.open_carnival()
        if screen is None:
            return {"status": "unavailable", "reason": "主页未显示美食嘉年华入口"}

        def tasks_page(frame):
            return carnival(frame) and selected_tab(frame, "任务", MAIN_TABS)

        screen = self.select(screen, "任务", MAIN_TABS, carnival)
        claimed = []
        for section in TASK_SECTIONS:
            self.report_progress(f"检查美食嘉年华{section}")
            screen = self.select(screen, section, TASK_TABS, tasks_page)
            screen, collected = self.claim(
                screen, section, lambda frame: tasks_page(frame) and selected_tab(frame, section, TASK_TABS),
            )
            if collected:
                claimed.append(section)

        self.report_progress("检查美食嘉年华等级奖励")
        screen = self.select(screen, "奖励", MAIN_TABS, carnival)
        _, collected = self.claim(
            screen, "等级奖励", lambda frame: carnival(frame) and selected_tab(frame, "奖励", MAIN_TABS),
        )
        if collected:
            claimed.append("等级奖励")
        if not claimed:
            return {"status": "already_complete", "reason": "美食嘉年华没有可领取的奖励"}
        return {"status": "complete", "claimed_sections": claimed}
