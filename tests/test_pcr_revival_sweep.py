import importlib
import re
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch


class EventUIError(RuntimeError):
    pass


class Frame:
    def __init__(self, *rows):
        self.items = [SimpleNamespace(text=text, center=(x, y)) for text, x, y in rows]

    def find(self, pattern, roi=(0, 0, 960, 540), exact=False):
        search = re.fullmatch if exact else re.search
        x1, y1, x2, y2 = roi
        return next(
            (item for item in self.items if x1 <= item.center[0] <= x2 and y1 <= item.center[1] <= y2
             and search(pattern, item.text)),
            None,
        )

    def text(self, roi):
        x1, y1, x2, y2 = roi
        return " ".join(item.text for item in self.items
                        if x1 <= item.center[0] <= x2 and y1 <= item.center[1] <= y2)

    def blue_button(self, item):
        return item is not None


class PCRRevivalSweepTest(unittest.TestCase):
    def setUp(self):
        self.revival = Mock()
        modules = {
            "pcrscript.game_ui.event_layout": SimpleNamespace(event_layout=lambda _: None),
            "pcrscript.game_ui.screen": SimpleNamespace(EventUIError=EventUIError,
                                                       normalized=lambda text: "".join(text.split())),
            "pcrscript.run_session": SimpleNamespace(clock=SimpleNamespace(time=lambda: 50, sleep=Mock())),
            "pcrscript.tasks": SimpleNamespace(BaseTask=object),
            "pcrscript.tasks.event_sweep": SimpleNamespace(HardSweep=Mock()),
            "pcrscript.tasks.revival_map": SimpleNamespace(RevivalMap=Mock()),
            "pcrscript.tasks.task_home": SimpleNamespace(ToHomePage=Mock()),
            "pcrscript.tasks.task_revival_event": SimpleNamespace(RevivalEventOnce=self.revival),
            "pcrscript.templates": SimpleNamespace(ImageTemplate=Mock()),
        }
        self.enterContext(patch.dict(sys.modules, modules))
        self.sweep = importlib.import_module("core.pcr_revival_sweep")
        self.ui = Mock()
        self.runner = SimpleNamespace(ui=self.ui, check_deadline=Mock(), log=Mock(), report={})
        self.flow = self.sweep.MapHardSweep(self.runner)
        self.ui.number.side_effect = lambda frame, roi: (
            int(item.text) if (item := frame.find(r"\d+", roi, exact=True)) else None
        )
        self.ui.read_region.side_effect = lambda frame, _roi: frame

    def detail(self, remaining, *, stage="1-3", tickets="120", stamina="90", after="70", count=1):
        return Frame((f"活动关卡{stage}", 196, 46), ("剩余挑战次数", 851, 388),
                     (f"{remaining}/3", 902, 414), (tickets, 860, 283),
                     (stamina, 683, 414), (after, 740, 414), (f"使用{count}张", 750, 333))

    def test_revival_entry_does_not_use_once_per_event_state(self):
        event = SimpleNamespace(startTimestamp=10, endTimestamp=90, name="复刻", extras={"event_id": 1})
        robot = SimpleNamespace(_event_news=SimpleNamespace(revival=event), _task_output="run/task")
        runner = self.revival.return_value
        runner.report = {}
        self.assertIs(self.sweep.enter_active_revival(robot), runner)
        self.revival.assert_called_once_with(robot, options={"collect_house_stamina": False, "output": "run/task"})
        runner.enter.assert_called_once_with()
        runner.run.assert_not_called()
        runner.set_event.assert_not_called()
        event.endTimestamp = 50
        self.assertIsNone(self.sweep.enter_active_revival(robot))

    def test_wrong_stage_and_inconsistent_preview_cannot_submit(self):
        for frame, reason in ((self.detail(1, stage="1-2"), "剩余次数"),
                              (self.detail(1, after="73"), "预览")):
            with self.subTest(reason=reason), self.assertRaisesRegex(EventUIError, reason):
                self.flow.sweep_stage(frame, "1-3")
        self.ui.click.assert_not_called()

    def test_known_shortage_skips_without_a_click(self):
        self.assertEqual(self.flow.sweep_stage(self.detail(2, tickets="0"), "1-3"), 0)
        self.assertIn("不足", self.runner.report["sweep_skipped"]["1-3"])
        self.ui.click.assert_not_called()

    def test_half_stamina_sweep_confirms_once_and_waits_for_updated_attempts(self):
        confirm = Frame(("扫荡券确认", 478, 141), ("要消耗扫荡券和体力通关关卡吗", 480, 227),
                        ("确认", 591, 370))
        result = Frame(("扫荡结果", 478, 40), ("跳过", 476, 475))
        self.ui.capture.side_effect = [self.detail(3, count=2, tickets="2", after="70"),
                                       confirm, confirm, result, self.detail(3), self.detail(1)]
        initial = self.detail(3, tickets="2", after="80")
        self.assertEqual(self.flow.sweep_stage(initial, "1-3"), 2)
        actions = [call.args[0] for call in self.ui.click.call_args_list]
        self.assertEqual([item if isinstance(item, tuple) else item.text for item in actions],
                         [(878, 333), "使用2张", "确认", "跳过"])
        self.assertIn("剩余 1 次", self.runner.report["sweep_skipped"]["1-3"])

    def test_replenish_prompt_never_confirms(self):
        self.ui.capture.return_value = Frame(("恢复挑战次数", 470, 144), ("取消", 370, 371),
                                             ("确认", 590, 371))
        with self.assertRaisesRegex(EventUIError, "停止消费"):
            self.flow.settle("1-3", 0)
        self.assertEqual([call.args[0].text for call in self.ui.click.call_args_list], ["取消"])
