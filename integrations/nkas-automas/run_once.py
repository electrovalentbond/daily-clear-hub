"""Run the due tasks of one NKAS v1.2.0 profile using its native scheduler."""

import os
import re
import signal
import sys
import traceback
from collections import Counter
from datetime import datetime
from pathlib import Path


MAX_ATTEMPTS_PER_TASK = 3


class RunError(Exception):
    pass


class QueueDrained(Exception):
    pass


def status(state, detail=""):
    message = f"DCH_NKAS_STATUS {state} {detail}".rstrip()
    path = os.environ.get("DAILY_CLEAR_HUB_NKAS_STATUS_PATH")
    if path:
        with Path(path).open("a", encoding="utf-8") as stream:
            stream.write(message + "\n")
    else:
        print(message, flush=True)


def validate_profile(root, profile):
    if not re.fullmatch(r"[^\x00-\x1f<>:\"/\\|?*.]{1,64}", profile):
        raise RunError("NKAS 实例名无效")
    if profile != profile.strip() or profile.lower().startswith("template"):
        raise RunError("请指定 NKAS 中已保存的实例名")
    if not (root / "main.py").is_file() or not (root / "module" / "config" / "config.py").is_file():
        raise RunError("当前目录缺少 NKAS 完整版文件")
    if not (root / "config" / f"{profile}.json").is_file():
        raise RunError("找不到指定的 NKAS 实例，请先在 NKAS 界面保存该实例")
    if not str(root).isascii():
        raise RunError("NKAS 安装目录需要使用英文路径")


def run_profile(profile):
    root = Path.cwd()
    validate_profile(root, profile)
    # The Windows toolkit runs this file directly from the hub. NKAS expects
    # imports and relative resources to resolve from the upstream directory.
    sys.path.insert(0, str(root))
    sys.argv[0] = str(root / "main.py")

    from main import NikkeAutoScript
    from module.base.resource import release_resources
    from module.config.serial_state import read_serial_config

    class FiniteScheduler(NikkeAutoScript):
        def __init__(self, config_name):
            super().__init__(config_name=config_name)
            self.attempts = Counter()
            self.due_tasks = set()
            self.finished = set()
            self.unresolved = set()
            self.game_ready = False
            self.login_interrupted_task = False
            self.cleaned = False

        def get_next_task(self):
            config = self.config
            if config.Client_Platform not in {"win", "adb"}:
                raise RunError("NKAS 实例平台需要为 Windows 客户端或 ADB")
            if config.Client_Platform == "win" and sys.platform == "win32":
                from ctypes import windll

                if not windll.shell32.IsUserAnAdmin():
                    raise RunError("Windows 游戏客户端需要以管理员权限运行 AUTO-MAS")
            serial = read_serial_config()
            if serial.enable and self.config_name in serial.group:
                raise RunError("请在 NKAS 中关闭此实例的串行模式，队列由 AUTO-MAS 调度")

            config.get_next_task()
            enabled = config.pending_task + config.waiting_task
            if not self.due_tasks and not any(task.command != "Restart" for task in enabled):
                raise RunError("请先在 NKAS 实例中至少启用一个任务")
            if any(not isinstance(task.next_run, datetime) for task in enabled):
                raise RunError("NKAS 实例的任务执行时间格式无效")
            known_tasks = {task.strip() for task in config.SCHEDULER_PRIORITY.split(">")}
            if any(task.command not in known_tasks for task in enabled):
                raise RunError("NKAS 实例包含无法识别的任务")

            self.due_tasks.update(task.command for task in config.pending_task if task.command != "Restart")
            if not config.pending_task:
                missing = (self.due_tasks - self.finished) | self.unresolved
                if missing:
                    raise RunError(f"仍有任务未完成（{', '.join(sorted(missing))}）")
                raise QueueDrained
            command = super().get_next_task()
            if (
                self.config.Client_Platform == "win"
                and not (self.is_first_task and command == "Restart")
                and not self.is_independent_task(command)
                and not self.config.PCClientInfo_LauncherPath
            ):
                raise RunError("NKAS 启动器路径为空，请在「通用配置 → PC 客户端」选择 nikke_launcher.exe")
            return command

        def start(self):
            # Upstream run() returns True if a task encountered a login screen
            # and was sent through startup. Its command still needs a retry.
            super().start()
            self.login_interrupted_task = True

        def run(self, command, skip_first_screenshot=False):
            task = self.config.task.command
            if self.attempts[task] >= MAX_ATTEMPTS_PER_TASK:
                raise RunError(f"{task} 连续调度三次后仍待执行")
            self.attempts[task] += 1
            status("task_started", task)
            self.login_interrupted_task = False

            game_task = not self.is_independent_task(command)
            if game_task and not self.game_ready and not skip_first_screenshot:
                # The native scheduler intentionally skips an initial Restart.
                # On ADB the device may therefore be ready before the app is.
                if not self.device.app_is_running():
                    super().start()
                self.game_ready = True

            success = super().run(command, skip_first_screenshot=skip_first_screenshot)
            success = success and not self.login_interrupted_task
            if success:
                self.unresolved.discard(task)
                if task != "Restart":
                    self.finished.add(task)
                if game_task:
                    self.game_ready = True
                status("task_ok", task)
            else:
                self.unresolved.add(task)
                status("task_retry", task)
            return success

        def _post_action(self):
            if not self.cleaned:
                self.cleaned = True
                super()._post_action()

        def _loop(self):
            try:
                super()._loop()
            finally:
                try:
                    self._post_action()
                finally:
                    release_resources()

    runner = FiniteScheduler(profile)
    status("started")
    try:
        runner.loop()
    except QueueDrained:
        return "complete" if runner.finished else "already_complete"
    finally:
        # The upstream session manager can own a physical ADB display. Finish
        # its cleanup before our terminal status, where errors affect the result.
        displays = sys.modules.get("module.device.adb.virtual_display_session")
        if displays is not None:
            displays.close_sessions()
    return "stopped"


def main(argv):
    if len(argv) != 1:
        status("failed", "需要一个 NKAS 实例名")
        return 2
    try:
        result = run_profile(argv[0])
    except KeyboardInterrupt:
        result = "stopped"
    except SystemExit as exc:
        if exc.code not in (None, 0):
            status("failed", "NKAS 执行失败，详见 NKAS 的 log 目录")
            return 1
        result = "stopped"
    except RunError as exc:
        status("failed", str(exc))
        return 1
    except Exception as exc:
        traceback.print_exc()
        status("failed", f"NKAS 内部错误 {type(exc).__name__}")
        return 1
    status(result)
    return 130 if result == "stopped" else 0


def interrupt(_signum, _frame):
    raise KeyboardInterrupt


if __name__ == "__main__":
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, interrupt)
    sys.exit(main(sys.argv[1:]))
