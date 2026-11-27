import itertools
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from scripts.uu_boost import BoostError, DesktopClient, Label, Page, boost


def label(text, x, y, role="", enabled=None):
    return Label(text, (x - 20, y - 9, x + 20, y + 9), role, enabled)


SEARCH = label("搜索游戏", 810, 49, "Edit")
RESULT = label("学园偶像大师", 810, 104, "ListItem")
STOP = label("停止加速", 223, 347)
START = label("立即加速", 223, 347)
LAUNCH = label("启动游戏", 95, 347)
CONFIRM = label("确定", 432, 456)
CANCEL = label("取消", 568, 456)
STOP_NOTICE = Label("重新加速，将断开正在加速游戏连接", (386, 352, 615, 371))
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
        target = detail(
            "学园偶像大师", STOP, LAUNCH, label("启动游戏", 95, 395),
            label("游戏服：日服", 410, 330),
        )
        client = TestClient(target, target)
        self.run_boost(client, region="日服")
        self.assertEqual(client.actions, [])

        client = TestClient(target, target)
        with patch.object(client, "page", wraps=client.page) as read_page:
            self.run_boost(client, region="日服", launch_game=True)
        self.assertEqual(read_page.call_count, 2)
        self.assertEqual(client.actions, [("click", LAUNCH)])

    def test_launch_requires_unambiguous_available_button_in_active_row(self):
        for controls, reason in (
            ((), "未识别到加速详情页上的「启动游戏」按钮"),
            ((LAUNCH, label("启动游戏", 155, 347)), "加速详情页有多个「启动游戏」按钮"),
            ((LAUNCH, label("启动游戏", 95, 347, "Button", False)), "「启动游戏」按钮不可用"),
            ((label("启动游戏", 95, 395),), "未识别到加速详情页上的「启动游戏」按钮"),
        ):
            with self.subTest(controls=controls):
                target = detail("学园偶像大师", STOP, *controls)
                client = TestClient(*([target] * 15))
                with self.assertRaisesRegex(BoostError, f"已加速，{reason}"):
                    self.run_boost(client, launch_game=True)
                self.assertEqual(client.actions, [])

    def test_launch_reports_click_failure_after_recognizing_exact_button(self):
        target = detail("学园偶像大师", STOP, LAUNCH)
        client = TestClient(target, target)
        with patch.object(client, "click", side_effect=BoostError("控件被其他窗口遮挡")) as click:
            with self.assertRaisesRegex(BoostError, "已识别「学园偶像大师」的「启动游戏」，点击失败"):
                self.run_boost(client, launch_game=True)
        click.assert_called_once_with(LAUNCH)

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
        stop_dialog = detail("边狱公司", STOP, STOP_NOTICE, CONFIRM, CANCEL)
        target = detail("学园偶像大师", STOP)
        client = TestClient(
            old, stop_dialog, page(), page(), page(), page(RESULT), target, target,
        )
        self.run_boost(client)
        self.assertEqual(client.actions, [
            ("click", STOP), ("click", CONFIRM), ("search", SEARCH, "学园偶像大师"),
            ("click", RESULT),
        ])

    def test_inherited_stop_confirmation_resumes_switch_or_keeps_target_active(self):
        target = detail("学园偶像大师", STOP, LAUNCH)
        old_dialog = detail("边狱公司", STOP, STOP_NOTICE, CONFIRM, CANCEL)
        client = TestClient(old_dialog, old_dialog, page(), page(), page(), page(RESULT), target, target)
        self.run_boost(client, launch_game=True)
        self.assertEqual(client.actions, [
            ("click", CONFIRM), ("search", SEARCH, "学园偶像大师"),
            ("click", RESULT), ("click", LAUNCH),
        ])

        target_dialog = detail("学园偶像大师", STOP, LAUNCH, STOP_NOTICE, CONFIRM, CANCEL)
        client = TestClient(target_dialog, target_dialog, target, target)
        self.run_boost(client, launch_game=True)
        self.assertEqual(client.actions, [("click", CANCEL), ("click", LAUNCH)])

    def test_alternate_stop_buttons_require_own_stop_request_and_modal_row(self):
        old = detail("边狱公司", STOP)
        notice = label("确定停止加速吗？", 500, 360)
        for confirm, cancel in (
            (label("停止加速", 432, 456), CANCEL),
            (label("确认停止", 568, 456), label("取消", 432, 456)),
        ):
            with self.subTest(confirm=confirm, cancel=cancel):
                dialog = detail("边狱公司", STOP, notice, confirm, cancel)
                target = detail("学园偶像大师", STOP)
                client = TestClient(old, dialog, page(), page(), page(), page(RESULT), target, target)
                self.run_boost(client)
                self.assertEqual(client.actions, [
                    ("click", STOP), ("click", confirm),
                    ("search", SEARCH, "学园偶像大师"), ("click", RESULT),
                ])

                client = TestClient(*([dialog] * 15))
                with self.assertRaisesRegex(BoostError, "停止加速确认仍显示"):
                    self.run_boost(client)
                self.assertEqual(client.actions, [])

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


class DesktopWindowTests(unittest.TestCase):
    def setUp(self):
        self.client = object.__new__(DesktopClient)
        self.client.rect = SimpleNamespace(left=10, top=20)
        self.client.window = Mock(handle=100)
        self.client.window.rectangle.return_value = self.client.rect
        self.client.window.is_minimized.return_value = False
        self.client.window_errors = (OSError, RuntimeError)
        self.client.gui = Mock()
        self.client.gui.GetForegroundWindow.return_value = 100
        self.client.gui.IsChild.side_effect = lambda main, hwnd: hwnd == 101
        self.client.get_ancestor = Mock(side_effect=lambda hwnd, flags: 100 if hwnd in {200, 300} else hwnd)
        self.client.window_thread_process = Mock(side_effect=lambda hwnd: (1, 8 if hwnd == 300 else 9))

    def test_owned_dialog_can_keep_foreground(self):
        self.client.gui.GetForegroundWindow.return_value = 200
        self.client._focus()
        self.client.window.set_focus.assert_not_called()

    def test_foreign_or_unrelated_foreground_never_counts_as_uu(self):
        for hwnd in (0, 300, 400):
            with self.subTest(hwnd=hwnd):
                self.client.gui.GetForegroundWindow.return_value = hwnd
                with self.assertRaisesRegex(BoostError, "未取得前台焦点"):
                    self.client._focus()

    def test_hit_target_must_be_main_child_or_same_process_owned_window(self):
        for hwnd in (100, 101, 200):
            self.client.gui.WindowFromPoint.return_value = hwnd
            self.assertEqual(self.client._point(LAUNCH), (105, 367))
        for hwnd in (0, 300, 400):
            self.client.gui.WindowFromPoint.return_value = hwnd
            with self.assertRaisesRegex(BoostError, "控件被其他窗口遮挡"):
                self.client._point(LAUNCH)


if __name__ == "__main__":
    unittest.main()
