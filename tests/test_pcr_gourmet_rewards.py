import importlib
import re
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch


class ScreenError(RuntimeError):
    pass


class BaseTask:
    def __init__(self, robot):
        self.robot = robot

    def report_progress(self, *_):
        pass


class Screen:
    def __init__(self, *labels, selected=(), enabled=True):
        self.labels = [SimpleNamespace(text=text, center=(x, y), score=.99) for text, x, y in labels]
        self.selected = selected
        self.enabled = enabled

    def find(self, pattern, roi=(0, 0, 960, 540), exact=False):
        match = re.fullmatch if exact else re.search
        left, top, right, bottom = roi
        return next(
            (label for label in self.labels if left <= label.center[0] <= right
             and top <= label.center[1] <= bottom and match(pattern, label.text)),
            None,
        )

    def blue_button(self, button):
        return button is not None and self.enabled


def carnival_screen(section, *, enabled):
    rewards = section == "等级奖励"
    tab = "奖励" if rewards else "任务"
    labels = [("美食嘉年华", 121, 34), ("任务", 793, 95), ("奖励", 906, 95),
              ("全部收取", 834, 420)]
    if not rewards:
        labels.extend([("每日任务", 371, 146), ("每周任务", 506, 146), ("挑战任务", 642, 146)])
    return Screen(*labels, selected=(tab, section), enabled=enabled)


class GourmetRewardsTest(unittest.TestCase):
    def setUp(self):
        self.ui = Mock()
        self.ui.read_region.side_effect = lambda screen, _roi: screen
        self.enterContext(patch.dict(sys.modules, {
            "pcrscript.game_ui.screen": SimpleNamespace(
                EventUI=lambda *_: self.ui, EventUIError=ScreenError, normalized=lambda text: text,
            ),
            "pcrscript.run_session": SimpleNamespace(clock=SimpleNamespace(sleep=Mock(), monotonic=Mock())),
            "pcrscript.tasks": SimpleNamespace(BaseTask=BaseTask),
        }))
        self.gourmet = importlib.import_module("core.pcr_gourmet_rewards")
        self.enterContext(patch.object(self.gourmet, "selected_tab", side_effect=lambda screen, name, _roi: name in screen.selected))
        self.task = self.gourmet.ClaimGourmetRewards(SimpleNamespace(driver=object()))
        self.home_labels = (("我的主页", 80, 523), ("主菜单", 875, 525), ("日程表", 755, 455))
        self.home = Screen(*self.home_labels, ("美食嘉年华", 580, 455))
        self.receipt = Screen(("获得奖励", 473, 114), ("关闭", 481, 400))

    def queue_waits(self, *candidates):
        waiting = iter(candidates)

        def wait(predicate, description, *, timeout):
            for frame in next(waiting):
                if predicate(frame):
                    return frame
            raise ScreenError(f"{description}超时")

        self.ui.wait.side_effect = wait

    def clicks(self):
        return [action.args[0].text for action in self.ui.click.call_args_list]

    def test_claims_task_and_level_rewards_and_verifies_each_receipt(self):
        sections = ("每日任务", "每周任务", "挑战任务", "等级奖励")
        frames = [(self.home,), (carnival_screen(sections[0], enabled=True),)]
        for index, section in enumerate(sections):
            if index:
                frames.append((carnival_screen(section, enabled=True),))
            frames.extend(((self.receipt,), (carnival_screen(section, enabled=False),)))
        self.queue_waits(*frames)

        self.assertEqual(self.task.run(), {"status": "complete", "claimed_sections": list(sections)})
        self.assertEqual(self.clicks(), ["美食嘉年华", "全部收取", "关闭", "每周任务", "全部收取", "关闭",
                                         "挑战任务", "全部收取", "关闭", "奖励", "全部收取", "关闭"])

    def test_missing_entry_on_verified_home_is_skipped_without_clicking(self):
        home = Screen(*self.home_labels)
        self.queue_waits((home,))
        self.ui.capture.return_value = home

        self.assertEqual(self.task.run()["status"], "unavailable")
        self.ui.click.assert_not_called()

    def test_rechecks_the_carnival_side_of_merged_home_labels(self):
        home = Screen(*self.home_labels, ("美食嘉年华究极炼成", 577, 458))
        home.labels[-1].box = [[510, 448], [644, 448], [644, 468], [510, 468]]
        self.ui.read_region.side_effect = None
        self.ui.read_region.return_value = Screen(("美食嘉年华", 545, 458))

        self.assertEqual(self.gourmet.home_entry(self.ui, home).center, (545, 458))
        self.ui.read_region.assert_called_once_with(home, (508, 445, 585, 471))

    def test_no_rewards_when_all_claim_buttons_are_disabled(self):
        self.queue_waits(*((carnival_screen(section, enabled=False),)
                           for section in ("每日任务", "每周任务", "挑战任务", "等级奖励")))

        self.assertEqual(self.task.run()["status"], "already_complete")
        self.assertEqual(self.clicks(), ["每周任务", "挑战任务", "奖励"])

    def test_unverified_claim_stops_after_one_submission(self):
        daily = carnival_screen("每日任务", enabled=True)
        self.queue_waits((daily,), (daily, daily))

        with self.assertRaisesRegex(ScreenError, "核对每日任务领奖结果"):
            self.task.run()
        self.assertEqual(self.clicks(), ["全部收取"])
