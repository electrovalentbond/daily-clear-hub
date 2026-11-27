import json
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.patch_maabh2 import patch_project


KNOWN_POPUPS = [
    "Hub_清弹窗_关闭公告",
    "Hub_清弹窗_关闭祈愿宣传",
    "Hub_清弹窗_领取每日签到",
]
HOME_MARKER = "检测主界面_标志"
WISH_RETURN = "Hub_清弹窗_退出祈愿"
WISH_BACK = "Hub_清弹窗_祈愿系统返回"
LOGIN_START = "国服进入游戏_开始"
LOGIN_UPDATE_WAIT = "国服进入游戏_等更新完成"
LOGIN_SCREEN = "进入游戏_识别切换账号"
LOGIN_GAME_UPDATE = "国服进入游戏_检测更新"
LOGIN_PROMPT = "Hub_进入游戏_点击继续"
POPUP_HANDOFF = "Hub_进入游戏_交接清弹窗"


class MaaBh2SetupTests(unittest.TestCase):
    def setUp(self):
        self.interface = Path(self.enterContext(TemporaryDirectory())) / "interface.json"
        self.popup = {"name": "3. 清理弹窗", "entry": "清理弹窗_入口", "default_check": True}
        self.daily = {"name": "10. 每日每周任务奖励领取", "entry": "每日_开始"}
        self.login = {"name": "11. 进入游戏（国服/腾讯服/测试服）", "entry": LOGIN_START}
        self.server_select = {"name": "2. 进入游戏（自选服务器）", "entry": "进入游戏_开始"}
        self.project = {
            "name": "MaaBh2", "version": "0.3.6",
            "task": [self.popup, self.daily, self.login, self.server_select],
        }

    def write_interface(self):
        self.interface.write_text(json.dumps(self.project, ensure_ascii=False), encoding="utf-8-sig")

    def test_handles_known_popups_before_generic_buttons_or_home_detection(self):
        self.popup["pipeline_override"] = {"清弹窗": {"timeout": 20000}}
        self.write_interface()

        self.assertTrue(patch_project(self.interface))
        updated = json.loads(self.interface.read_text(encoding="utf-8"))
        self.assertEqual(updated["task"][1], self.daily)
        overrides = updated["task"][0].pop("pipeline_override")
        unchanged_fields = {key: value for key, value in self.popup.items() if key != "pipeline_override"}
        self.assertEqual(updated["task"][0], unchanged_fields)
        self.assertEqual(overrides["清弹窗"]["timeout"], 20000)
        self.assertEqual(overrides["清弹窗"]["next"], [
            *KNOWN_POPUPS, WISH_RETURN, WISH_BACK,
            "关掉x", "领取", "清弹窗_点领取奖励", "生日弹窗", HOME_MARKER, "首页",
        ])
        self.assertEqual(overrides["清弹窗"]["on_error"], [HOME_MARKER, "首页"])
        for name in ("检测主界面", "检测主界面_终"):
            self.assertEqual(overrides[name]["next"], [*KNOWN_POPUPS, WISH_RETURN, WISH_BACK, HOME_MARKER, "首页"])
            self.assertEqual(overrides[name]["on_error"], [HOME_MARKER, "首页"])
        self.assertEqual(overrides["首页"]["next"], ["清弹窗"])
        self.assertEqual(overrides["首页"]["recognition"]["param"]["template"], ["shouye"])
        for node_name in KNOWN_POPUPS:
            with self.subTest(node=node_name):
                node = overrides[node_name]
                self.assertEqual(node["action"]["type"], "Click")
                self.assertEqual(node["next"], ["清弹窗"])
                self.assertGreater(node["max_hit"], 0)

        notice, wish, sign_in = (overrides[name]["recognition"] for name in KNOWN_POPUPS)
        for recognition, template in ((notice, "popup_x/关闭.png"), (wish, "popup_x/关闭2.png")):
            self.assertEqual(recognition["type"], "TemplateMatch")
            self.assertEqual(recognition["param"]["template"], [template])
            self.assertIn("roi", recognition["param"])
        self.assertEqual(sign_in["type"], "And")
        sign_in_params = sign_in["param"]
        title, button = sign_in_params["all_of"]
        self.assertEqual(title["recognition"], "OCR")
        self.assertEqual(title["expected"], ["^每日签到$"])
        self.assertEqual(button["recognition"], "TemplateMatch")
        self.assertEqual(button["template"], ["btn_lingqu.png"])
        self.assertNotEqual(title["roi"], button["roi"])
        self.assertEqual(sign_in_params["box_index"], 1)

    def test_wish_recovery_targets_the_return_button_and_rescans_for_home(self):
        self.write_interface()
        self.assertTrue(patch_project(self.interface))
        overrides = json.loads(self.interface.read_text(encoding="utf-8"))["task"][0]["pipeline_override"]
        promo = overrides[KNOWN_POPUPS[1]]
        self.assertEqual(promo["action"]["param"]["target_offset"], [22, 18, -49, -45])

        exit_node = overrides[WISH_RETURN]
        self.assertEqual(exit_node["recognition"]["type"], "And")
        params = exit_node["recognition"]["param"]
        wish_page, return_button = params["all_of"]
        self.assertEqual(params["box_index"], 1)
        self.assertEqual(return_button["recognition"], "OCR")
        self.assertRegex("返 回", return_button["expected"][0])
        self.assertNotRegex("返回首页", return_button["expected"][0])
        self.assertEqual(return_button["roi"][0:2], [0, 0])
        self.assertEqual(exit_node["action"], {"type": "Click", "param": {"target_offset": [0, 0, 0, 0]}})
        self.assertEqual(exit_node["next"], ["清弹窗"])
        self.assertEqual(exit_node["max_hit"], 3)

        back = overrides[WISH_BACK]
        self.assertEqual(back["recognition"], {"type": "Or", "param": {"any_of": wish_page["any_of"]}})
        self.assertEqual(back["action"], {"type": "ClickKey", "param": {"key": 4}})
        self.assertEqual(back["next"], ["清弹窗"])
        self.assertEqual(back["max_hit"], 2)
        wish_sections, special_title = wish_page["any_of"]
        self.assertEqual(wish_sections["recognition"], "And")
        record, draw = wish_sections["all_of"]
        self.assertRegex("祈愿记录", record["expected"][0])
        self.assertNotRegex("祈愿公告", record["expected"][0])
        self.assertRegex("祈愿10次", draw["expected"][0])
        self.assertRegex("全神器超绝祈愿", special_title["expected"][0])
        self.assertNotRegex("祈愿公告", special_title["expected"][0])

        claim_text = overrides["领取"]["recognition"]["param"]["all_of"][1]
        self.assertEqual(claim_text["roi"], "btn")
        self.assertRegex("领 取", claim_text["expected"][0])
        self.assertNotRegex("点击领取奖励", claim_text["expected"][0])
        self.assertNotRegex("前往祈愿", claim_text["expected"][0])

    def test_login_routes_through_guarded_start_or_handoff(self):
        self.login["pipeline_override"] = {LOGIN_START: {"pre_delay": 500}}
        self.write_interface()
        self.assertTrue(patch_project(self.interface))

        popup_task, daily, login_task, server_select = json.loads(self.interface.read_text(encoding="utf-8"))["task"]
        self.assertEqual(daily, self.daily)
        self.assertEqual(server_select, self.server_select)
        overrides = login_task["pipeline_override"]
        self.assertEqual(overrides[LOGIN_START]["pre_delay"], 500)
        self.assertEqual(overrides[LOGIN_START]["timeout"], 60000)
        self.assertEqual(overrides[LOGIN_START]["next"], [
            POPUP_HANDOFF, LOGIN_GAME_UPDATE, LOGIN_PROMPT, LOGIN_SCREEN,
        ])
        self.assertEqual(overrides[LOGIN_UPDATE_WAIT]["timeout"], 300000)
        self.assertEqual(overrides[LOGIN_UPDATE_WAIT]["next"], [POPUP_HANDOFF, LOGIN_PROMPT, LOGIN_SCREEN])
        self.assertEqual(overrides[LOGIN_SCREEN]["timeout"], 60000)
        self.assertEqual(overrides[LOGIN_SCREEN]["repeat"], 1)
        self.assertEqual(overrides[LOGIN_SCREEN]["pre_delay"], 0)
        self.assertEqual(overrides[LOGIN_SCREEN]["max_hit"], 4)
        self.assertEqual(overrides[LOGIN_SCREEN]["next"], [POPUP_HANDOFF, LOGIN_PROMPT, LOGIN_SCREEN])

        prompt = overrides[LOGIN_PROMPT]
        recognition = prompt["recognition"]
        self.assertEqual(recognition["type"], "OCR")
        x, y, width, height = recognition["param"]["roi"]
        self.assertTrue(x <= 640 < x + width and 550 <= y < 668 < y + height <= 720)
        patterns = recognition["param"]["expected"]
        for text, expected in (
            ("抚摸屏幕继续", True), ("点击屏幕进入游戏", True), ("轻触进入游戏", True),
            ("点击领取奖励", False), ("禁止进入游戏", False), ("账号切换", False),
        ):
            with self.subTest(text=text):
                self.assertEqual(any(re.search(pattern, text) is not None for pattern in patterns), expected)
        self.assertEqual(prompt["action"], {"type": "Click", "param": {"target": [640, 668]}})
        self.assertEqual(prompt["post_delay"], 2000)
        self.assertEqual(prompt["max_hit"], 4)
        self.assertEqual(prompt["next"], [POPUP_HANDOFF, LOGIN_PROMPT, LOGIN_SCREEN])

        handoff = overrides[POPUP_HANDOFF]
        self.assertEqual(handoff["recognition"]["type"], "Or")
        self.assertEqual(handoff["action"], {"type": "DoNothing"})
        self.assertFalse(handoff.get("next"))
        known_screens = handoff["recognition"]["param"]["any_of"]
        self.assertEqual(known_screens[0], HOME_MARKER)
        self.assertEqual(known_screens[1:], [
            {"recognition": popup_task["pipeline_override"][node_name]["recognition"]}
            for node_name in KNOWN_POPUPS
        ])

    def test_upgrades_previously_patched_project_without_discarding_custom_fields(self):
        self.popup["pipeline_override"] = {
            KNOWN_POPUPS[1]: {
                "action": {"type": "Click", "param": {"target_offset": [18, 16, -36, -32]}},
                "focus": {"Node.PipelineNode.Succeeded": "已关闭崩坏学园 2 祈愿宣传"},
            },
            "清弹窗": {
                "timeout": 20000,
                "next": [*KNOWN_POPUPS, "关掉x", "领取", "清弹窗_点领取奖励", "生日弹窗", HOME_MARKER],
                "on_error": [HOME_MARKER, "首页"],
            },
            "检测主界面": {"next": [*KNOWN_POPUPS, HOME_MARKER]},
            "检测主界面_终": {
                "next": [*KNOWN_POPUPS, HOME_MARKER],
                "on_error": [HOME_MARKER, "拉回主界面"],
                "pre_delay": 2500,
            },
            "领取": {"max_hit": 2},
        }
        self.write_interface()
        self.assertTrue(patch_project(self.interface))

        updated = json.loads(self.interface.read_text(encoding="utf-8"))
        overrides = updated["task"][0]["pipeline_override"]
        self.assertEqual(overrides["领取"]["max_hit"], 2)
        self.assertEqual(overrides["清弹窗"]["timeout"], 20000)
        self.assertEqual(overrides["清弹窗"]["on_error"], [HOME_MARKER, "首页"])
        self.assertEqual(overrides["清弹窗"]["next"][:5], [*KNOWN_POPUPS, WISH_RETURN, WISH_BACK])
        self.assertEqual(overrides[KNOWN_POPUPS[1]]["action"]["param"]["target_offset"], [22, 18, -49, -45])
        self.assertEqual(overrides["检测主界面_终"]["pre_delay"], 2500)
        self.assertEqual(overrides["检测主界面_终"]["on_error"], [HOME_MARKER, "首页"])
        self.assertIn(POPUP_HANDOFF, updated["task"][2]["pipeline_override"])
        before = self.interface.read_bytes()
        self.assertFalse(patch_project(self.interface))
        self.assertEqual(self.interface.read_bytes(), before)

    def test_migrates_existing_login_routes_to_include_title_prompt(self):
        self.login["pipeline_override"] = {
            LOGIN_START: {"timeout": 60000, "next": [POPUP_HANDOFF, LOGIN_GAME_UPDATE, LOGIN_SCREEN]},
            LOGIN_UPDATE_WAIT: {"timeout": 300000, "next": [POPUP_HANDOFF, LOGIN_SCREEN]},
            LOGIN_SCREEN: {"timeout": 60000, "next": [POPUP_HANDOFF], "rate_limit": 600},
        }
        self.write_interface()
        self.assertTrue(patch_project(self.interface))

        updated = json.loads(self.interface.read_text(encoding="utf-8"))
        overrides = updated["task"][2]["pipeline_override"]
        self.assertEqual(overrides[LOGIN_START]["next"], [
            POPUP_HANDOFF, LOGIN_GAME_UPDATE, LOGIN_PROMPT, LOGIN_SCREEN,
        ])
        self.assertEqual(overrides[LOGIN_UPDATE_WAIT]["next"], [POPUP_HANDOFF, LOGIN_PROMPT, LOGIN_SCREEN])
        self.assertEqual(overrides[LOGIN_SCREEN]["next"], [POPUP_HANDOFF, LOGIN_PROMPT, LOGIN_SCREEN])
        self.assertEqual(overrides[LOGIN_SCREEN]["rate_limit"], 600)
        before = self.interface.read_bytes()
        self.assertFalse(patch_project(self.interface))
        self.assertEqual(self.interface.read_bytes(), before)

    def test_does_not_replace_existing_different_routing(self):
        for node, field in (("检测主界面_终", "on_error"), ("清弹窗", "next")):
            with self.subTest(node=node, field=field):
                self.popup["pipeline_override"] = {node: {field: ["自定义路由"]}}
                self.write_interface()
                before = self.interface.read_bytes()

                with self.assertRaisesRegex(ValueError, "已有不同"):
                    patch_project(self.interface)
                self.assertEqual(self.interface.read_bytes(), before)

    def test_conflicting_login_routes_leave_the_whole_project_unchanged(self):
        self.login["pipeline_override"] = {LOGIN_START: {"next": ["自定义登录"]}}
        self.write_interface()
        before = self.interface.read_bytes()

        with self.assertRaisesRegex(ValueError, "已有不同"):
            patch_project(self.interface)
        self.assertEqual(self.interface.read_bytes(), before)

    def test_unsupported_version_is_not_modified(self):
        self.project["version"] = "0.3.7"
        self.write_interface()
        before = self.interface.read_bytes()

        with self.assertRaisesRegex(ValueError, r"MaaBH2.*0\.3\.6"):
            patch_project(self.interface)
        self.assertEqual(self.interface.read_bytes(), before)
