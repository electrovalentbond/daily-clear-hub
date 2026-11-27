from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction


INSTALL_CONFIG = Path(__file__).with_name("local.json")
JOB = Path(__file__).with_name("job.py")
TASKS = {
    "claim_idle_reward",
    "claim_gifts_new",
    "adventure_forces",
    "adventure_intercept",
    "expedition",
    "daily_pack",
    "claim_missions",
}
TASK_STATUS = {
    "done": "上游报告完成",
    "skipped": "上游报告跳过",
    "blocked": "游戏阻止了任务，请检查窗口内的提示和连接状态",
    "failed": "上游报告失败，请检查游戏界面与模型配置",
    "incomplete": "上游达到执行上限，任务未完成",
    "partial": "上游报告部分完成，请查看仍未完成的游戏项目",
    "wrong_scene": "游戏不在预期界面，请回到游戏主页后重试",
    "error": "上游执行异常，请检查游戏与模型配置",
    "setup": "上游依赖未就绪，请重新运行 setup-windows.ps1 -Games dotabyss",
    "model": "未读到有效的本机模型配置，请在 MaaDotAbyss 模型页保存并选择多模态模型",
    "window": "无法连接已选的 DMM 游戏窗口，请打开游戏并保持在桌面上",
    "resolution": "请在游戏内将窗口分辨率设为 1280×720",
}


def installed_paths() -> tuple[Path, Path]:
    try:
        installation = json.loads(INSTALL_CONFIG.read_text(encoding="utf-8-sig"))
        hub = Path(installation["hub_root"])
        upstream = Path(installation["dotabyss_root"])
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise ValueError("无法读取本机安装路径，请重新安装 Dot Abyss 接入并同步来源") from exc
    if not (
        hub.is_absolute() and (hub / "core" / "scheduler.py").is_file()
        and upstream.is_absolute() and (upstream / "dotabyss_agent" / "runner.py").is_file()
        and (upstream / "tasks" / "daily.yaml").is_file()
        and (upstream / ".venv" / "Scripts" / "python.exe").is_file()
    ):
        raise ValueError("找不到 Hub、MaaDotAbyss 源码或其 Python 环境，请重新安装并同步来源")
    return hub, upstream


def execute_task(context, task: str) -> str:
    hub, upstream = installed_paths()
    tasker = context.tasker
    info = tasker.controller.info
    hwnd = info.get("hwnd")
    if info.get("type") != "win32" or type(hwnd) is not int or hwnd <= 0:
        raise ValueError("AUTO-MAS 没有提供已绑定的 DMM 游戏窗口")

    sys.path.insert(0, str(hub))
    try:
        from core.scheduler import run_command
    finally:
        sys.path.pop(0)

    python = upstream / ".venv" / "Scripts" / "python.exe"
    with TemporaryDirectory(prefix="daily-clear-dotabyss-") as directory:
        result_path = Path(directory) / "result.json"
        command = [str(python), "-I", "-X", "utf8", str(JOB), task, str(hwnd), str(result_path)]
        # Raw upstream output can contain model responses or connection information.
        code = run_command(
            command, upstream, 720, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            cancelled=lambda: tasker.stopping,
        )
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"MaaDotAbyss 没有返回任务结果（退出码 {code}）") from exc
    if not isinstance(result, dict) or result.get("task") != task:
        raise ValueError("MaaDotAbyss 返回的任务结果与当前任务不符")
    status = result.get("status")
    if not isinstance(status, str) or status not in TASK_STATUS:
        raise ValueError("MaaDotAbyss 返回未知的任务状态")
    if code != 0 and status in {"done", "skipped"}:
        raise ValueError(f"MaaDotAbyss 未正常退出（退出码 {code}）")
    return status


@AgentServer.custom_action("DailyClearDotAbyss")
class DailyClearDotAbyss(CustomAction):
    def run(self, context, argv):
        try:
            payload = json.loads(getattr(argv, "custom_action_param", "") or "null")
            task = payload.get("task") if isinstance(payload, dict) else None
            if not isinstance(task, str) or task not in TASKS:
                raise ValueError("AUTO-MAS 的 Dot Abyss 任务参数无效")
            print(f"开始 Dot Abyss 任务 {task}", flush=True)
            status = execute_task(context, task)
        except subprocess.TimeoutExpired:
            print("Dot Abyss 任务执行超时", flush=True)
            return False
        except ValueError as exc:
            print(f"Dot Abyss 任务失败，{exc}", flush=True)
            return False
        except (ImportError, OSError, RuntimeError):
            print("Dot Abyss 任务未能运行或已停止，请检查本机安装与调度状态", flush=True)
            return False
        print(f"Dot Abyss 任务 {task}，{TASK_STATUS[status]}", flush=True)
        return status in {"done", "skipped"}


if __name__ == "__main__":
    if len(sys.argv) < 2 or not AgentServer.start_up(sys.argv[-1]):
        raise SystemExit("Dot Abyss Agent 无法启动，请从 AUTO-MAS 运行托管")
    try:
        AgentServer.join()
    finally:
        AgentServer.shut_down()
