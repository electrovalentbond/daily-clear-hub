from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryFile

from core.config_loader import PROJECT_ROOT, GameConfig


def _python_path(game: GameConfig) -> Path:
    # 虚拟环境可能把解释器链接到系统 Python，运行时要保留虚拟环境的路径。
    return PROJECT_ROOT / game.string("executable")


def check_hka(game: GameConfig) -> None:
    executable = _python_path(game)
    if not executable.is_file():
        raise ValueError(f"HKA Python 解释器不存在：{executable}")
    if not executable.name.lower().startswith("python"):
        raise ValueError("HKA executable 应指向 Python 解释器")

    project_dir = game.path("project_dir")
    if not (project_dir / "hka" / "__main__.py").is_file():
        raise ValueError(f"HKA 源码目录缺少 hka/__main__.py：{project_dir}")

    config_path = game.path("hka_config")
    if not config_path.is_file():
        raise ValueError(f"HKA 配置文件不存在：{config_path}")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"HKA 配置文件应为无 BOM 的 UTF-8 JSON：{config_path}") from exc
    if not isinstance(config, dict):
        raise ValueError(f"HKA 配置文件应为 JSON 对象：{config_path}")
    if config.get("version") != 1 or not isinstance(config.get("tasks"), list):
        raise ValueError("HKA 配置应使用 version 1 并包含 tasks 数组")
    emulator = config.get("emulator")
    if not isinstance(emulator, dict) or not all(
        isinstance(emulator.get(key), str) and emulator[key].strip()
        for key in ("adb_path", "serial", "package")
    ):
        raise ValueError("HKA 配置缺少有效的 emulator.adb_path、serial 或 package")


def run_hka(game: GameConfig, run_command: Callable[..., int]) -> None:
    command = [
        str(_python_path(game)),
        "-X",
        "utf8",
        "-m",
        "hka",
        "--config",
        str(game.path("hka_config")),
        "run",
    ]
    with TemporaryFile() as output:
        code = run_command(command, game.path("project_dir"), game.timeout, stdout=output)
        output.seek(0)
        stdout = output.read().decode("utf-8-sig", errors="replace")

    # HKA writes progress logs before its unindented JSON report.
    json_start = stdout.rfind("\n{") + 1
    try:
        report = json.loads(stdout[json_start:])
    except json.JSONDecodeError:
        report = None
    status = report.get("status") if isinstance(report, dict) else None
    if not isinstance(status, str):
        raise ValueError(f"HKA 未输出有效的最终运行报告（退出码 {code}）")
    if code != 0 or status not in ("success", "nothing_to_do"):
        raise ValueError(f"HKA 运行结束，状态 {status}（退出码 {code}）")
    print("HKA 按已配置流程执行完成" if status == "success" else "HKA 确认无需运行任务")
