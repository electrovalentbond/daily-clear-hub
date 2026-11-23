import io
import json
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from core.config_loader import GameConfig
from core.hka_backend import check_hka, run_hka


class HKABackendTest(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.project = Path(directory.name).resolve()
        self.executable = self.project / "python.exe"
        self.executable.touch()
        self.config = self.project / "config.json"
        self.config.write_text(json.dumps({
            "version": 1,
            "emulator": {"adb_path": "adb", "serial": "auto", "package": "example.package"},
            "tasks": [],
        }), encoding="utf-8")
        package = self.project / "hka"
        package.mkdir()
        (package / "__main__.py").touch()
        self.game = GameConfig(
            name="崩坏学园2",
            enabled=True,
            backend="hka",
            timeout=60,
            options={
                "executable": str(self.executable),
                "project_dir": str(self.project),
                "hka_config": str(self.config),
            },
        )

    def runner(self, body, code=0):
        def run_command(command, cwd, timeout, *, stdout):
            self.assertEqual(
                [str(self.executable), "-X", "utf8", "-m", "hka", "--config", str(self.config), "run"],
                command,
            )
            self.assertEqual(self.project, cwd)
            self.assertEqual(60, timeout)
            stdout.write(body.encode("utf-8"))
            return code

        return run_command

    def test_preflight_validates_hka_layout_and_json(self):
        check_hka(self.game)
        self.config.write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "JSON 对象"):
            check_hka(self.game)
        self.config.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "version 1"):
            check_hka(self.game)
        self.config.write_text("{}", encoding="utf-8-sig")
        with self.assertRaisesRegex(ValueError, "无 BOM"):
            check_hka(self.game)
        self.config.unlink()
        with self.assertRaisesRegex(ValueError, "配置文件不存在"):
            check_hka(self.game)
        self.executable.unlink()
        with self.assertRaisesRegex(ValueError, "解释器不存在"):
            check_hka(self.game)

    def test_accepts_terminal_reports_after_logging(self):
        for status in ("success", "nothing_to_do"):
            with self.subTest(status=status), redirect_stdout(io.StringIO()) as output:
                result = json.dumps({"status": status, "tasks": [{"name": "领奖"}]}, indent=2)
                run_hka(self.game, self.runner("运行日常\r\n" + result + "\r\n"))
                self.assertIn("HKA", output.getvalue())

    def test_preserves_virtual_environment_python_link(self):
        interpreter = self.project / "python3"
        interpreter.touch()
        self.executable.unlink()
        try:
            self.executable.symlink_to(interpreter)
        except OSError:
            self.skipTest("当前系统不允许建立符号链接")
        check_hka(self.game)
        with redirect_stdout(io.StringIO()):
            run_hka(self.game, self.runner('{"status": "nothing_to_do"}'))

    def test_does_not_accept_unverified_run(self):
        cases = (
            ('{ "status": "cancelled" }', 0, "cancelled"),
            ('{ "status": "failed" }', 1, "failed"),
            ('{ "status": "success" }', 1, "退出码 1"),
            ('{ "status": "success" }\n程序异常', 0, "最终运行报告"),
            ('启动失败', 0, "最终运行报告"),
            ('[]', 0, "最终运行报告"),
        )
        for body, code, detail in cases:
            with self.subTest(body=body, code=code):
                with self.assertRaisesRegex(ValueError, detail):
                    run_hka(self.game, self.runner(body, code))

    def test_timeout_propagates(self):
        def run_command(command, cwd, timeout, *, stdout):
            raise subprocess.TimeoutExpired(command, timeout)

        with self.assertRaises(subprocess.TimeoutExpired):
            run_hka(self.game, run_command)
