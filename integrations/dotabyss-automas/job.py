"""Run one task in the installed MaaDotAbyss environment on the selected window."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


WIN32_GUIDANCE = (
    "当前控制方式只支持截图与前台点击。请按画面操作，使用 click、skip、wait、wait_stable 或 report；"
    "界面树和自动连打程序不可用，不能调用 auto、observe 或 click_path。"
    "若起始画面还在加载，请等待。若确认是已登录的游戏标题页，只点击明确的开始或轻触提示，进入主页后执行任务。"
    "若需要从 DMM 登录、输入验证码或完成首次教程，请报告失败。"
    "战斗任务可逐次处理明确显示的免费次数，看不清剩余次数或完成状态时报告失败。"
    "只确认本任务目标所需的操作。遇到任何收费或恢复次数窗口时取消。"
)


def task_status(task: str, hwnd: int) -> str:
    sys.path.insert(0, str(Path.cwd()))
    try:
        from dotabyss_agent.brain import Brain
        from dotabyss_agent.device import DeviceError, GameDevice, Toolkit
        from dotabyss_agent.runner import run_selected
        from openai import OpenAIError
    except (ImportError, OSError):
        return "setup"

    class BoundGameDevice(GameDevice):
        @staticmethod
        def _find_window(title):
            # Reuse upstream Win32 capture/input while keeping AUTO-MAS's exact selection.
            return next((window for window in Toolkit.find_desktop_windows()
                         if getattr(window.hwnd, "value", window.hwnd) == hwnd and window.window_name == title
                         and window.class_name == "UnityWndClass"), None)

    class Win32Brain(Brain):
        def decide(self, task_prompt, knowledge, history, frame_bgr, supplement=""):
            guidance = WIN32_GUIDANCE
            if task != "claim_idle_reward":
                guidance += "出现装备自动分解确认时取消并报告失败。"
            if supplement:
                guidance = f"{supplement}\n{guidance}"
            return super().decide(task_prompt, knowledge, history, frame_bgr, supplement=guidance)

    try:
        brain = Win32Brain()
    except (KeyError, OSError, ValueError, OpenAIError):
        return "model"

    try:
        device = BoundGameDevice()
        if not device.ctrl.set_screenshot_use_raw_size(True):
            return "window"
        device.bring_to_front()
        if device.screenshot().shape[:2] != (720, 1280):
            return "resolution"
    except DeviceError:
        return "window"

    results = run_selected([task], update_knowledge=False, log=lambda message: None,
                           _device=device, _brain=brain)
    if len(results) != 1 or results[0].get("task") != task:
        return "error"
    return results[0].get("status", "error")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("task")
    parser.add_argument("hwnd", type=int)
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    try:
        status = task_status(args.task, args.hwnd)
    except Exception:
        status = "error"
    args.result.write_text(json.dumps({"task": args.task, "status": status}), encoding="utf-8")


if __name__ == "__main__":
    main()
