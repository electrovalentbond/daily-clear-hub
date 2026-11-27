import itertools
import unittest
from unittest.mock import patch

from scripts.uu_boost import BoostError, Label, Page, boost


def label(text, x, y, role=""):
    return Label(text, (x - 20, y - 9, x + 20, y + 9), role)


SEARCH = label("搜索游戏", 810, 49, "Edit")
RESULT = label("学园偶像大师", 810, 104, "ListItem")
STOP = label("停止加速", 223, 347)
START = label("立即加速", 223, 347)
CONFIRM = label("确定", 432, 456)


def page(*labels):
    return Page(1000, 688, (SEARCH, *labels))


def detail(game, button, *labels):
    return page(label(game, 150, 290), button, label("网络监控", 916, 332), *labels)


class TestClient:
    def __init__(self, *pages):
        self.pages = iter(pages)
        self.actions = []

    def attach(self, deadline):
        pass

    def page(self):
        return next(self.pages)

    def enter_search(self, field, value):
        self.actions.append(("search", field, value))

    def click(self, target):
        self.actions.append(("click", target))


class UuBoostTests(unittest.TestCase):
    def run_boost(self, client, *, region=""):
        with patch("scripts.uu_boost.time.sleep"), patch(
            "scripts.uu_boost.time.monotonic", side_effect=itertools.count()
        ):
            boost(client, "学园偶像大师", "学园偶像大师", region, 15)

    def test_search_ignores_partial_name_and_same_name_outside_suggestions(self):
        same_name_tile = label("学园偶像大师", 150, 390)
        different_region = label("学园偶像大师国际服", 810, 120)
        search_page = page(same_name_tile, different_region)
        self.assertIsNone(search_page.search_result(SEARCH, "学园偶像大师"))
        self.assertEqual(
            page(same_name_tile, different_region, RESULT).search_result(SEARCH, "学园偶像大师"),
            RESULT,
        )

    def test_switches_verified_active_page_then_waits_for_the_result(self):
        old = detail("边狱公司", STOP)
        stop_dialog = detail(
            "边狱公司", STOP,
            label("重新加速，将断开正在加速游戏连接", 500, 360),
            CONFIRM, label("取消", 567, 456),
        )
        target = detail("学园偶像大师", STOP)
        client = TestClient(
            old, stop_dialog, page(), page(), page(), page(RESULT), target, target,
        )
        self.run_boost(client)
        self.assertEqual(client.actions, [
            ("click", STOP), ("click", CONFIRM), ("search", SEARCH, "学园偶像大师"),
            ("click", RESULT),
        ])

    def test_stop_dialog_with_purchase_never_clicks_confirm(self):
        old = detail("边狱公司", STOP)
        warning = detail(
            "边狱公司", STOP,
            label("重新加速，将断开正在加速游戏连接", 500, 360),
            label("订阅收费会员", 500, 390),
            CONFIRM, label("取消", 567, 456),
        )
        client = TestClient(old, *([warning] * 20))
        with self.assertRaises(BoostError):
            self.run_boost(client)
        self.assertEqual(client.actions, [("click", STOP)])

    def test_explicit_region_has_to_be_visible_on_the_active_game_page(self):
        active = detail("学园偶像大师", STOP, label("游戏服：智能匹配", 410, 330))
        client = TestClient(active, active)
        self.run_boost(client, region="智能匹配")
        self.assertEqual(client.actions, [])
        unknown = detail("学园偶像大师", STOP, label("智能匹配", 410, 330))
        client = TestClient(*([unknown] * 20))
        with self.assertRaisesRegex(BoostError, "未能验证当前区服"):
            self.run_boost(client, region="智能匹配")
        self.assertEqual(client.actions, [])

    def test_region_picker_requires_labeled_exact_option_and_starts_after_selection(self):
        selector = label("游戏服：亚服", 410, 330)
        region = label("日服", 510, 340)
        chosen = label("游戏服：日服", 410, 330)
        target = detail("学园偶像大师", STOP, chosen)
        client = TestClient(
            detail("学园偶像大师", START, selector),
            page(label("选择区服", 480, 250), label("日服测试服", 510, 300), region),
            detail("学园偶像大师", START, chosen), target, target,
        )
        self.run_boost(client, region="日服")
        self.assertEqual(client.actions, [("click", selector), ("click", region), ("click", START)])


if __name__ == "__main__":
    unittest.main()
