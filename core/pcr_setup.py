from __future__ import annotations

import os
import subprocess
from dataclasses import replace
from pathlib import Path
from shutil import which

from core.config_loader import GameConfig


PCR_PACKAGE = "com.bilibili.priconne"
_MANUAL_FIELDS = {"project_dir", "executable", "pcr_config"}


def _find_adb(tools_root: Path) -> Path | None:
    candidates = [tools_root / "platform-tools" / "adb.exe"]
    if on_path := which("adb"):
        candidates.append(Path(on_path))
    for key in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        if sdk := os.environ.get(key):
            candidates.append(Path(sdk) / "platform-tools" / "adb.exe")
    if system_drive := os.environ.get("SystemDrive"):
        drive_root = Path(f"{system_drive}/")
        for folder in ("leidian", "LDPlayer"):
            candidates.append(drive_root / folder / "LDPlayer9" / "adb.exe")
    return next((path.resolve() for path in candidates if path.is_file()), None)


def _adb_output(adb: Path, *arguments: str) -> str:
    result = subprocess.run(
        [str(adb), *arguments], stdin=subprocess.DEVNULL, capture_output=True,
        encoding="utf-8", errors="replace", timeout=5,
    )
    return result.stdout if result.returncode == 0 else ""


def _find_target(adb: Path, requested: str) -> str | None:
    serials = []
    for line in _adb_output(adb, "devices").splitlines():
        serial, _, state = line.partition("\t")
        if state.strip() == "device" and serial and (not requested or serial == requested):
            serials.append(serial)
    matches = []
    for serial in dict.fromkeys(serials):
        output = _adb_output(adb, "-s", serial, "shell", "pm", "path", PCR_PACKAGE)
        if any(line.startswith("package:/") for line in output.splitlines()):
            matches.append(serial)
    if len(matches) > 1:
        raise ValueError(
            "多个已连接的 ADB 设备安装了公主连结国服 B 服，请只保留目标设备，"
            "或设置 games.pcr.adb_serial。"
        )
    return matches[0] if matches else None


def discover_pcr(game: GameConfig, tools_root: Path) -> GameConfig | None:
    if game.backend == "pcr_script" and _MANUAL_FIELDS.intersection(game.options):
        return game

    project = (tools_root / "pcr-script").resolve()
    python = project / ".venv" / "Scripts" / "python.exe"
    if not python.is_file() or not (project / "daily_task.py").is_file():
        return None
    adb = _find_adb(tools_root)
    if adb is None:
        return None
    requested = game.options.get("adb_serial", "")
    if not isinstance(requested, str):
        raise ValueError("games.pcr.adb_serial 应为字符串")
    try:
        serial = _find_target(adb, requested.strip())
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError(f"无法使用 {adb} 检查公主连结模拟器") from exc
    if serial is None:
        return None

    timeout = game.timeout if game.backend == "pcr_script" else 1800
    return replace(game, backend="pcr_script", timeout=timeout, options={
        **game.options,
        "project_dir": str(project),
        "executable": str(python),
        "_pcr_runtime_config": {
            "Extra": {"adb_path": str(adb), "adb_serial": serial, "dnpath": ""},
            "Gift": {"auto_dismantle": False},
            "Task": {1: [["schedule"], ["get_quest_reward"], ["get_gift", True]]},
        },
    })
