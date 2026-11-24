import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.patch_maabh2 import patch_popup_task


class MaaBh2SetupTests(unittest.TestCase):
    def setUp(self):
        self.interface = Path(self.enterContext(TemporaryDirectory())) / "interface.json"
        self.popup = {"name": "3. 清理弹窗", "entry": "清理弹窗_入口", "default_check": True}
        self.daily = {"name": "10. 每日每周任务奖励领取", "entry": "每日_开始"}
        self.project = {"name": "MaaBh2", "version": "0.3.6", "task": [self.popup, self.daily]}

    def write_interface(self):
        self.interface.write_text(json.dumps(self.project, ensure_ascii=False), encoding="utf-8-sig")

    def test_rechecks_home_after_popup_timeout_and_after_last_click(self):
        self.popup["pipeline_override"] = {"清弹窗": {"timeout": 20000}}
        self.write_interface()

        self.assertTrue(patch_popup_task(self.interface))
        updated = json.loads(self.interface.read_text(encoding="utf-8"))
        self.assertEqual(updated["task"][1], self.daily)
        self.assertEqual(updated["task"][0], {
            **self.popup,
            "pipeline_override": {
                "清弹窗": {"timeout": 20000, "on_error": ["检测主界面_标志", "首页"]},
                "检测主界面_终": {"on_error": ["检测主界面_标志", "拉回主界面"]},
            },
        })
        before = self.interface.read_bytes()
        self.assertFalse(patch_popup_task(self.interface))
        self.assertEqual(self.interface.read_bytes(), before)

    def test_does_not_replace_an_existing_different_fallback(self):
        self.popup["pipeline_override"] = {"检测主界面_终": {"on_error": ["自定义回退"]}}
        self.write_interface()
        before = self.interface.read_bytes()

        with self.assertRaisesRegex(ValueError, "已有不同"):
            patch_popup_task(self.interface)
        self.assertEqual(self.interface.read_bytes(), before)

    def test_unsupported_version_is_not_modified(self):
        self.project["version"] = "0.3.7"
        self.write_interface()
        before = self.interface.read_bytes()

        with self.assertRaisesRegex(ValueError, "MaaBH2 0.3.6"):
            patch_popup_task(self.interface)
        self.assertEqual(self.interface.read_bytes(), before)
