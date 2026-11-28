import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.patch_maagakumas import patch


class GakumasShutdownTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory()))
        self.interface = self.root / "interface.json"
        self.android = self.root / "resource/base/pipeline/Shutdown.json"
        self.dmm = self.root / "resource/DMM/pipeline/Shutdown.json"
        self.dmm_startup = self.dmm.with_name("StartUp.json")
        self.android.parent.mkdir(parents=True)
        self.dmm.parent.mkdir(parents=True)
        self.project = {
            "name": "MaaGakumasu",
            "version": "v1.5.4",
            "interface_version": 2,
            "resource": [
                {"name": "官服", "path": ["./resource/base"], "controller": ["模拟器", "PlayCover"]},
                {"name": "插件版汉化", "path": ["./resource/base", "./resource/zh_CN"],
                 "controller": ["模拟器", "PlayCover"]},
                {"name": "DMM", "path": ["./resource/base", "./resource/DMM"], "controller": ["PC"]},
                {"name": "DMM插件汉化版", "path": ["./resource/base", "./resource/zh_CN", "./resource/DMM"],
                 "controller": ["PC"]},
            ],
        }
        self.android_pipeline = {
            "Shutdown": {
                "recognition": {"type": "DirectHit", "param": {}},
                "action": {"type": "StopApp", "param": {"package": "com.bandainamcoent.idolmaster_gakuen"}},
            },
        }
        self.write_interface()
        self.write_json(self.android, self.android_pipeline)
        self.write_json(self.dmm_startup, {"StartUpStartGame": {"action": {"type": "DoNothing"}}})

    @staticmethod
    def write_json(path, data, encoding="utf-8"):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding=encoding)

    def write_interface(self):
        self.write_json(self.interface, self.project, encoding="utf-8-sig")

    def test_adds_dmm_shutdown_overlay_without_changing_base_or_interface(self):
        unchanged = {path: path.read_bytes() for path in (self.interface, self.android, self.dmm_startup)}

        self.assertTrue(patch(self.interface))
        self.assertEqual(
            json.loads(self.dmm.read_text(encoding="utf-8")),
            {"Shutdown": {"action": {"type": "StopApp", "param": {"package": ""}}}},
        )
        installed = self.dmm.read_bytes()
        self.assertFalse(patch(self.interface))
        self.assertEqual(self.dmm.read_bytes(), installed)
        for path, content in unchanged.items():
            self.assertEqual(path.read_bytes(), content)

    def test_requires_both_pc_resources(self):
        resources = self.project["resource"]
        for absent in ("DMM", "DMM插件汉化版"):
            with self.subTest(resource=absent):
                self.project["resource"] = [resource for resource in resources if resource["name"] != absent]
                self.write_interface()
                with self.assertRaises(ValueError):
                    patch(self.interface)
                self.assertFalse(self.dmm.exists())

    def test_rejects_an_overlay_shared_with_an_android_resource(self):
        self.project["resource"][0]["path"].append("./resource/DMM")
        self.write_interface()
        with self.assertRaises(ValueError):
            patch(self.interface)
        self.assertFalse(self.dmm.exists())

    def test_rejects_an_unexpected_base_shutdown_node(self):
        self.android_pipeline["Shutdown"]["action"]["param"]["package"] = "com.example.other"
        self.write_json(self.android, self.android_pipeline)
        with self.assertRaises(ValueError):
            patch(self.interface)
        self.assertFalse(self.dmm.exists())

    def test_preserves_an_incompatible_existing_dmm_overlay(self):
        self.write_json(self.dmm, {"Shutdown": {"action": {"type": "DoNothing"}}})
        before = self.dmm.read_bytes()
        with self.assertRaises(ValueError):
            patch(self.interface)
        self.assertEqual(self.dmm.read_bytes(), before)
