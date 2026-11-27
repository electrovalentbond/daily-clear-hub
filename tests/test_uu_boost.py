import itertools
import unittest
from unittest.mock import patch

from scripts.uu_boost import BoostError, Label, Page, boost


def label(text, x, y, role="", enabled=None):
    return Label(text, (x - 20, y - 9, x + 20, y + 9), role, enabled)


SEARCH = label("搜索游戏", 810, 49, "Edit")
RESULT = label("学园偶像大师", 810, 104, "ListItem")
STOP = label("停止加速", 223, 347)
START = label("立即加速", 223, 347)
LAUNCH = label("启动游戏", 95, 347)
CONFIRM = label("确定", 432, 456)
NAVIGATION = (label("首页", 182, 50), label("游戏", 260, 50), label("云存档", 345, 50))
HOME_CARD = Label("学园偶像大师", (92, 429, 207, 456))
HOME_START = label("立即加速", 148, 375)


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

    def hover(self, target):
        self.actions.append(("hover", target))


class UuBoostTests(unittest.TestCase):
    def run_boost(self, client, *, region="", launch_game=False):
        with patch("scripts.uu_boost.time.sleep"), patch(
            "scripts.uu_boost.time.monotonic", side_effect=itertools.count()
        ), patch("builtins.print"):
            boost(client, "学园偶像大师", "学园偶像大师", region, 15, launch_game=launch_game)

    def test_launch_is_opt_in_and_clicks_once_on_verified_game_and_region(self):
        target = detail("学园偶像大师", STOP, LAUNCH, label("游戏服：日服", 410, 330))
        client = TestClient(target, target)
        self.run_boost(client, region="日服")
        self.assertEqual(client.actions, [])

        client = TestClient(target, target)
        with patch.object(client, "page", wraps=client.page) as read_page:
            self.run_boost(client, region="日服", launch_game=True)
        self.assertEqual(read_page.call_count, 2)
        self.assertEqual(client.actions, [("click", LAUNCH)])

    def test_launch_requires_unambiguous_available_button_in_active_row(self):
        for controls in (
            (),
            (LAUNCH, label("启动游戏", 155, 347)),
            (LAUNCH, label("启动游戏", 95, 347, "Button", False)),
            (label("启动游戏", 95, 395),),
        ):
            with self.subTest(controls=controls):
                target = detail("学园偶像大师", STOP, *controls)
                client = TestClient(*([target] * 15))
                with self.assertRaisesRegex(BoostError, "已加速，未识别到唯一可用的「启动游戏」按钮"):
                    self.run_boost(client, launch_game=True)
                self.assertEqual(client.actions, [])

    def test_launch_stays_blocked_during_purchase_prompt_or_other_game(self):
        target = detail("学园偶像大师", STOP, LAUNCH, label("立即购买", 500, 390))
        client = TestClient(*([target] * 15))
        with self.assertRaisesRegex(BoostError, "确认、登录或会员提示"):
            self.run_boost(client, launch_game=True)
        self.assertEqual(client.actions, [])

        other = detail("边狱公司", STOP, LAUNCH)
        client = TestClient(*([other] * 15))
        with self.assertRaisesRegex(BoostError, "旧加速会话未停止"):
            self.run_boost(client, launch_game=True)
        self.assertEqual(client.actions, [("click", STOP)])

    def test_search_finds_custom_header_without_dynamic_wallpaper_tab(self):
        current_query = label("Q学园偶像大师", 815, 49)
        stale_query = label("Q其他游戏", 804, 50)
        unrelated_edit = label("修改昵称", 420, 85, "Edit")
        header = Page(1000, 688, (*NAVIGATION, current_query, unrelated_edit))
        self.assertEqual(header.search("学园偶像大师"), current_query)
        header = Page(1000, 688, (*NAVIGATION, stale_query, unrelated_edit))
        self.assertEqual((header.search("学园偶像大师").x, header.search("学园偶像大师").y), (820, 50))

    def test_full_search_results_use_the_single_exact_card_left_of_search_box(self):
        result_header = (
            label("搜索结果", 80, 140), label("共2个搜索结果", 355, 145),
        )
        card = label("学园偶像大师", 355, 398)
        partial = label("学园偶像大师模拟器", 500, 398)
        full_results = page(*NAVIGATION, *result_header, card, partial)
        target = detail("学园偶像大师", STOP)
        client = TestClient(page(), full_results, target, target)
        self.run_boost(client)
        action, selected = client.actions[1]
        self.assertEqual(client.actions[0], ("search", SEARCH, "学园偶像大师"))
        self.assertEqual((action, selected.text, selected.x), ("click", card.text, card.x))
        self.assertLess(selected.y, card.y)
        self.assertIsNone(full_results.search_result(SEARCH, "学园偶像"))
        duplicate = label("学园偶像大师", 510, 398)
        self.assertIsNone(page(*result_header, card, duplicate, RESULT).search_result(SEARCH, card.text))

    def test_uses_verified_start_on_same_name_home_card(self):
        home_labels = (*NAVIGATION, label("我的游戏（80）", 880, 535), HOME_CARD)
        home = Page(1000, 688, home_labels)
        other_start = label("立即加速", 383, 375)
        hovered = Page(1000, 688, (*home_labels, HOME_START, other_start))
        target = detail("学园偶像大师", STOP)
        client = TestClient(home, hovered, target, target)
        self.run_boost(client)
        action, cover = client.actions[0]
        self.assertEqual((action, cover.x, cover.y), ("hover", HOME_CARD.x, 334))
        self.assertEqual(client.actions[1:], [("click", HOME_START)])

    def test_explicit_region_does_not_quick_start_from_home(self):
        home = page(*NAVIGATION, label("我的游戏", 880, 535), HOME_CARD, HOME_START)
        target = detail("学园偶像大师", STOP, label("游戏服：日服", 410, 330))
        client = TestClient(home, page(RESULT), target, target)
        self.run_boost(client, region="日服")
        self.assertEqual(client.actions, [("search", SEARCH, "学园偶像大师"), ("click", RESULT)])

    def test_reports_missing_search_field_before_attempting_to_match_a_game(self):
        client = TestClient(*([Page(1000, 688, ())] * 15))
        with self.assertRaisesRegex(BoostError, "未识别到 UU 搜索框"):
            self.run_boost(client)
        self.assertEqual(client.actions, [])

    def test_retries_search_if_first_input_yields_no_results(self):
        target = detail("学园偶像大师", STOP)
        client = TestClient(*([page()] * 5), page(RESULT), target, target)
        self.run_boost(client)
        self.assertEqual(client.actions, [
            ("search", SEARCH, "学园偶像大师"), ("search", SEARCH, "学园偶像大师"), ("click", RESULT),
        ])

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
