"""Claim the free dialogue reward in the CN alchemy room."""

from __future__ import annotations

from pcrscript.game_ui.screen import EventUI, EventUIError, normalized
from pcrscript.run_session import clock as time
from pcrscript.tasks import BaseTask
from pcrscript.templates import ImageTemplate


HOME_ENTRY = (510, 398, 710, 478)
ROOM_CONTENT = (25, 66, 935, 403)
REWARD_PANEL = (270, 330, 690, 418)
STORY_PROMPT = (205, 65, 755, 340)
STORY_CONFIRM = (480, 300, 745, 500)
STORY_LINE = (175, 418, 795, 487)
STORY_ARROW = (751, 475, 811, 523)
STORY_ACTION_DELAY = 1.6
SKIP_TEXT = r"剧情梗概|(?:剧情|对话)跳过|跳过(?:这个|这段|这次|此段|该段|当前)?(?:剧情|对话|对白|视频)"


def in_room(screen):
    return bool(
        screen.find("究极炼成", (44, 12, 193, 62), exact=True)
        and screen.find("相册", (548, 23, 678, 75), exact=True)
        and screen.find("道具一览", (631, 23, 770, 75), exact=True)
    )


def in_home(screen):
    return bool(
        screen.find("我的主页", (25, 496, 155, 540), exact=True)
        and screen.find("礼物", (860, 400, 950, 475), exact=True)
        and screen.find("日程表|任务", (687, 400, 882, 475), exact=True)
    )


def dialogue_marker(image):
    """Match the yellow stem/dot and outlined bubble in the room, at several sizes."""
    import cv2 as cv
    import numpy as np

    left, top, right, bottom = ROOM_CONTENT
    hsv = cv.cvtColor(image[top:bottom, left:right], cv.COLOR_BGR2HSV)
    yellow = cv.inRange(hsv, (14, 175, 185), (36, 255, 255))
    _, _, stats, centers = cv.connectedComponentsWithStats(yellow)
    dots = [row for row in stats[1:] if 3 <= row[3] <= 19 and .62 <= row[2] / row[3] <= 1.5]
    matches = []
    for index, (x, y, width, height, area) in enumerate(stats[1:], 1):
        if not (9 <= height <= 48 and .24 <= width / height <= .68 and area >= .44 * width * height):
            continue
        center = centers[index][0]
        for dot_x, dot_y, dot_width, dot_height, dot_area in dots:
            if not (
                .19 * height <= dot_height <= .48 * height
                and 0 <= dot_y - (y + height) <= .36 * height
                and -.48 * height <= (dot_x + dot_width / 2) - center <= .20 * height
                and dot_area >= .52 * dot_width * dot_height
            ):
                continue
            patch = hsv[max(0, y - height // 4):dot_y + dot_height + height // 4,
                        max(0, round(center - .85 * height)):round(center + .85 * height)]
            hue, saturation, brightness = cv.split(patch)
            pale = (saturation <= 170) & (brightness >= 177)
            outline = (hue >= 8) & (hue <= 36) & (saturation >= 130) & (brightness < 180)
            if float(np.mean(pale)) >= .24 and float(np.mean(outline)) >= .05:
                matches.append((left + round(center), top + int(y + height // 2)))
    return matches[0] if len(matches) == 1 else None


def reward_visible(screen):
    return bool(
        screen.find("炼成|阿尔凯斯", REWARD_PANEL)
        and screen.find("获得|收取|得到了", REWARD_PANEL)
    )


def story_advance(image):
    """Recognize the small pink, downward-facing arrow on the dialogue panel."""
    import cv2 as cv
    import numpy as np

    left, top, right, bottom = STORY_ARROW
    hsv = cv.cvtColor(image[top:bottom, left:right], cv.COLOR_BGR2HSV)
    mask = cv.inRange(hsv, (136, 25, 173), (179, 160, 255))
    _, labels, stats, centers = cv.connectedComponentsWithStats(mask)
    candidates = []
    for index, (x, y, width, height, area) in enumerate(stats[1:], 1):
        if not (9 <= width <= 25 and 6 <= height <= 18 and 1.15 <= width / height <= 2.2):
            continue
        if not .40 <= area / (width * height) <= .78:
            continue
        component = labels[y:y + height, x:x + width] == index
        upper = np.count_nonzero(component[:height // 2])
        lower = np.count_nonzero(component[-height // 2:])
        if upper > 1.4 * lower:
            center_x, center_y = centers[index]
            candidates.append((left + round(center_x), top + round(center_y)))
    return candidates[0] if len(candidates) == 1 else None


class ClaimAlchemyReward(BaseTask):
    def __init__(self, robot):
        super().__init__(robot)
        self.ui = EventUI(robot.driver, self.task_options().get("output", "cache/daily/alchemy_reward"))
        self.story_skip = ImageTemplate("btn_skip", threshold=.86, roi=(850, 0, 950, 80))

    def wait_through_story(self, predicate, description, *, timeout):
        skip_requested = False
        skip_confirmed = False
        last_advanced_line = None
        advances_on_line = 0
        action_after = 0.0

        def ready(screen):
            nonlocal skip_requested, skip_confirmed, last_advanced_line, advances_on_line, action_after
            now = time.monotonic()
            if screen.find(SKIP_TEXT, STORY_PROMPT):
                if not skip_confirmed and (button := screen.find("确定|确认|跳过", STORY_CONFIRM, exact=True)):
                    self.ui.save("alchemy_story_confirm", screen)
                    self.ui.click(button)
                    skip_confirmed = True
                    action_after = now + STORY_ACTION_DELAY
                return False
            if not screen.battle_dialogue():
                return predicate(screen)
            if now < action_after or screen.find("确定|确认|取消", STORY_CONFIRM, exact=True):
                return False

            advance = story_advance(screen.image)
            line = normalized(screen.text(STORY_LINE)) if advance else ""
            if last_advanced_line and line and line != last_advanced_line:
                last_advanced_line = None
                advances_on_line = 0
                skip_requested = False
                skip_confirmed = False

            if not (skip_requested or skip_confirmed) and (button := self.story_skip.match(screen.image)):
                self.ui.save("alchemy_story_skip", screen)
                self.ui.click(button)
                skip_requested = True
                action_after = now + STORY_ACTION_DELAY
            elif advance and line and advances_on_line < 2:
                # Some room dialogues retain the skip icon but ignore a tap.
                # Advance only when the scene exposes its own continue arrow.
                self.ui.save("alchemy_story_advance", screen)
                self.ui.click(advance)
                last_advanced_line = line
                advances_on_line += 1
                action_after = now + STORY_ACTION_DELAY
            return False

        return self.ui.wait(ready, description, timeout=timeout)

    def find_dialogue_marker(self):
        marker = None
        deadline = None
        empty_frames = 0

        def ready(screen):
            nonlocal marker, deadline, empty_frames
            if reward_visible(screen):
                return True
            if not in_room(screen):
                deadline = None
                empty_frames = 0
                return False
            marker = dialogue_marker(screen.image)
            if marker is not None:
                return True
            now = time.monotonic()
            if deadline is None:
                deadline = now + 7
            empty_frames += 1
            return empty_frames >= 2 and now >= deadline

        screen = self.wait_through_story(ready, "识别炼金堂对话气泡", timeout=100)
        return screen, marker

    def run(self):
        self.report_progress("寻找究极炼成入口")
        screen = self.ui.wait(lambda view: in_home(view) or in_room(view), "识别首页或炼金堂", timeout=20)
        if not in_room(screen):
            entry = screen.find("究极炼成", HOME_ENTRY, exact=True)
            if entry is None:
                entry = self.ui.read_region(screen, HOME_ENTRY).find("究极炼成", HOME_ENTRY, exact=True)
            if entry is None:
                self.ui.save("alchemy_entry_unavailable", screen)
                return {"status": "unavailable", "reason": "首页未识别到究极炼成入口，请确认玩法已解锁"}
            self.ui.click(entry)

        self.report_progress("检查炼金堂角色对话气泡")
        screen, marker = self.find_dialogue_marker()
        if marker is None:
            if reward_visible(screen):
                self.ui.save("alchemy_reward", screen)
                return {"status": "complete"}
            self.ui.save("alchemy_no_marker", screen)
            return {"status": "unavailable", "reason": "已进入炼金堂，未检测到可领取的对话气泡"}

        self.ui.save("alchemy_dialogue_marker", screen)
        self.report_progress("领取炼金堂奖励并核对回执")
        self.ui.click(marker, delay=.35)
        try:
            receipt = self.wait_through_story(reward_visible, "核对究极炼成对话奖励", timeout=100)
        except EventUIError as error:
            return {"status": "blocked", "reason": str(error)}
        self.ui.save("alchemy_reward", receipt)
        return {"status": "complete"}
