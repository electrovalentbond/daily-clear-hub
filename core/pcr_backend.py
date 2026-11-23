from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from shutil import which
from tempfile import TemporaryDirectory, TemporaryFile

import yaml

from core.config_loader import PROJECT_ROOT, GameConfig


VERIFIED_TASK_STATUSES = {"complete", "already_complete", "unavailable"}


def _python_path(game: GameConfig) -> Path:
    # 保留虚拟环境解释器链接，子进程以该链接所在目录识别虚拟环境。
    return PROJECT_ROOT / game.string("executable")


def _config_payload(game: GameConfig) -> object:
    if "_pcr_runtime_config" in game.options:
        return game.options["_pcr_runtime_config"]
    config_path = game.path("pcr_config")
    try:
        return yaml.safe_load(config_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ValueError(f"无法读取 pcr-script 配置：{config_path}（{exc}）") from exc


def check_pcr(game: GameConfig) -> None:
    python = _python_path(game)
    if not python.is_file() or not python.name.lower().startswith("python"):
        raise ValueError(f"请将 executable 指向 pcr-script 的 Python 解释器：{python}")

    project = game.path("project_dir")
    required = ("daily_task.py", "pcrscript/runtime.py", "images/btn_ok.png")
    for relative in required:
        if not (project / relative).is_file():
            raise ValueError(f"pcr-script 源码目录缺少 {relative}：{project}")

    config = _config_payload(game)
    if not isinstance(config, dict):
        raise ValueError("pcr-script 配置应为 YAML 映射")

    task_groups = config.get("Task")
    if not isinstance(task_groups, dict) or len(task_groups) != 1:
        raise ValueError("pcr-script 日常命令只读取第一组任务，请在 Task 中保留一组任务")
    tasks = next(iter(task_groups.values()))
    if not isinstance(tasks, list) or not tasks or not all(
        isinstance(row, list) and row and isinstance(row[0], str) and row[0].strip()
        for row in tasks
    ):
        raise ValueError("pcr-script 的 Task 应为非空任务列表，例如 Task: {1: [[schedule]]}")

    extra = config.get("Extra", {})
    if not isinstance(extra, dict) or not all(
        isinstance(extra.get(key, ""), str)
        for key in ("dnpath", "adb_path", "adb_serial", "adb_unicode_console_path")
    ):
        raise ValueError("pcr-script 的 Extra 应包含字符串类型的设备设置")
    dnpath = extra.get("dnpath", "").strip()
    if dnpath:
        console = project / dnpath / "ldconsole.exe"
        if not console.is_file():
            raise ValueError(f"pcr-script 找不到雷电控制台：{console}")
    else:
        adb = extra.get("adb_path", "").strip() or "adb"
        if not (project / adb).is_file() and not which(adb):
            raise ValueError(f"pcr-script 找不到 ADB，请检查 Extra.adb_path：{adb}")


def run_pcr(game: GameConfig, run_command: Callable[..., int]) -> None:
    if "_pcr_runtime_config" not in game.options:
        _run_cli(game, run_command, game.path("pcr_config"))
        return
    with TemporaryDirectory(prefix="daily-clear-pcr-") as directory:
        config_path = Path(directory) / "daily_config.yml"
        config_path.write_text(
            yaml.safe_dump(_config_payload(game), allow_unicode=True),
            encoding="utf-8",
        )
        _run_cli(game, run_command, config_path)


def _run_cli(game: GameConfig, run_command: Callable[..., int], config_path: Path) -> None:
    command = [
        str(_python_path(game)), "-X", "utf8", "-u", "daily_task.py",
        "--config", str(config_path),
    ]
    with TemporaryFile() as output:
        code = run_command(command, game.path("project_dir"), game.timeout, stdout=output)
        output.seek(0)
        stdout = output.read().decode("utf-8", errors="replace")

    # 日志在前，命令行约定最后输出一个带业务状态的 JSON 对象。
    json_start = stdout.rfind("\n{") + 1
    try:
        report = json.loads(stdout[json_start:])
    except json.JSONDecodeError:
        report = None
    if not isinstance(report, dict):
        raise ValueError(f"pcr-script 未返回最终 JSON 报告（退出码 {code}）；请查看上游 cache/daily/runs")

    tasks = report.get("tasks")
    valid_tasks = isinstance(tasks, list) and bool(tasks) and all(
        isinstance(task, dict)
        and isinstance(task.get("task"), str)
        and isinstance(task.get("status"), str)
        for task in tasks
    )
    if not valid_tasks:
        raise ValueError(f"pcr-script 没有可核实的任务结果（退出码 {code}）；请查看上游 cache/daily/runs")
    for task in tasks:
        print(f"  {task['task']}  {task['status']}", flush=True)
    if code or report.get("status") != "complete" or report.get("verified") is not True or any(
        task["status"] not in VERIFIED_TASK_STATUSES for task in tasks
    ):
        status = report.get("status")
        raise ValueError(f"pcr-script 本轮任务未全部核实完成，报告状态 {status}（退出码 {code}）；请查看上游 cache/daily/runs")
