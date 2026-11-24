import importlib
import re
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch


class Frame:
    def __init__(self, *labels, blue=True):
        self.items = [SimpleNamespace(text=text, center=(x, y), score=.99) for text, x, y in labels]
        self.enabled = blue

    def find(self, pattern, roi, exact=False):
        match = re.fullmatch if exact else re.search
        left, top, right, bottom = roi
        return next((item for item in self.items if left <= item.center[0] <= right
                     and top <= item.center[1] <= bottom and match(pattern, item.text)), None)

    def blue_button(self, button):
        return self.enabled and button is not None


class UIError(RuntimeError):
    pass


class BaseTask:
    def __init__(self, robot):
        self.robot = robot

    def report_progress(self, _):
        pass


class VeryHardSweepTests(unittest.TestCase):
    def setUp(self):
        self.ui = Mock()
        runner = SimpleNamespace(ui=self.ui, layout="map")
        self.hub = Frame(("活动关卡", 557, 202), ("讨伐证交换", 616, 334), ("首领挑战券", 750, 120))
        self.list = Frame(("活动关卡", 557, 202), ("讨伐证交换", 616, 334), ("首领挑战券", 750, 120),
                          ("高难", 739, 282), ("30张来挑战", 868, 282))
        self.detail = Frame(("BOSS详情", 120, 45), ("高难", 255, 45), ("击败1只", 755, 372),
                            ("首领挑战券数量", 650, 424), ("取消", 666, 462))
        self.preview = Frame(("扫荡券确认", 478, 142), ("确认", 592, 369), ("取消", 367, 369))
        self.result = Frame(("扫荡结果", 478, 42), ("确认", 477, 479))
        self.enter = Mock(return_value=runner)
        self.enterContext(patch.dict(sys.modules, {
            "core.pcr_revival_sweep": SimpleNamespace(enter_active_revival=self.enter),
            "pcrscript.game_ui.event_layout": SimpleNamespace(legacy_hub=lambda s: s is self.hub or s is self.list),
            "pcrscript.game_ui.screen": SimpleNamespace(EventUIError=UIError, normalized=lambda text: text),
            "pcrscript.tasks": SimpleNamespace(BaseTask=BaseTask),
            "pcrscript.tasks.revival_map": SimpleNamespace(RevivalMap=lambda _: SimpleNamespace(hub=lambda: self.hub)),
        }))
        self.sweep = importlib.import_module("core.pcr_vh_sweep")
        self.task = self.sweep.SweepVeryHardBoss(object())

    def serve(self, captures, waiting, numbers):
        self.ui.capture.side_effect = captures
        self.ui.number.side_effect = numbers
        frames = iter(waiting)

        def wait(predicate, description, *, timeout):
            frame = next(frames)
            if not predicate(frame):
                raise UIError(description)
            return frame

        self.ui.wait.side_effect = wait

    def clicks(self):
        return [record.args[0].text for record in self.ui.click.call_args_list]

    def test_scrolls_to_vh_and_submits_once_with_confirmed_cost(self):
        self.serve([self.list, self.detail], [self.detail, self.preview, self.result, self.result, self.detail, self.hub],
                   [89, 59, 27])
        self.assertEqual(self.task.run(), {"status": "complete", "swept": 1})
        self.assertEqual(self.clicks(), ["高难", "击败1只", "确认", "确认", "取消"])
        self.ui.swipe.assert_called_once()

    def test_unexpected_cost_blocks_before_spending(self):
        self.serve([self.list], [self.detail], [89, 29, 27])
        self.assertEqual(self.task.run()["status"], "blocked")
        self.assertEqual(self.clicks(), ["高难"])

    def test_multi_sweep_dialog_is_cancelled(self):
        self.preview.items.append(SimpleNamespace(text="扫荡2次", center=(500, 244), score=.99))
        self.serve([self.list], [self.detail, self.preview], [89, 59, 27])
        self.assertEqual(self.task.run()["status"], "blocked")
        self.assertEqual(self.clicks(), ["高难", "击败1只", "取消"])

    def test_daily_counter_anchors_label_and_rejects_lifetime_count(self):
        self.assertIsNone(self.sweep.remaining_today(Frame(("讨伐次数0/1", 902, 47))))
        self.assertIsNone(self.sweep.remaining_today(Frame(("剩余挑战次数10/1", 902, 47))))
        self.assertIsNone(self.sweep.remaining_today(Frame(("剩余挑战次数0/1其他", 902, 47))))
        self.assertEqual(self.sweep.remaining_today(Frame(("剩余挑战次数0/1", 902, 47))), 0)
        self.assertEqual(self.sweep.remaining_today(Frame(("剩余挑战次数", 740, 47), ("1/1", 902, 47))), 1)
