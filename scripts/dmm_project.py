"""Add a DMM shortcut pretask to an installed MaaFramework project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TASK_NAME = "DailyClearHubDmmLaunch"
OPTION_NAME = "DailyClearHubDmmLaunchSettings"
CONTROLLERS = {"gakumas": "PC", "dotabyss": "Win32Front"}


def prepare(game: str, path: Path) -> bool:
    project = json.loads(path.read_text(encoding="utf-8-sig"))
    original = project.get("pretask") or []
    if isinstance(original, dict):
        original = [original]
    launch = {
        "name": TASK_NAME,
        "label": "启动 DMM 游戏",
        "description": "通过 DMM 官方快捷方式打开游戏并等待窗口。已运行的窗口会直接复用。",
        "controller": [CONTROLLERS[game]],
        "exec": "powershell",
        "args": [
            "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
            "-File", "{PROJECT_DIR}/daily-clear-dmm.ps1", "-Game", game,
        ],
        "option": [OPTION_NAME],
    }
    settings = {
        "type": "input",
        "label": "DMM 启动设置",
        "inputs": [
            {"name": "shortcut", "label": "DMM 游戏快捷方式完整路径（可留空）", "default": ""},
        ],
    }
    # The UU variant prepends its own pretask when copying this interface.
    pretasks = [launch, *(task for task in original if task.get("name") != TASK_NAME)]
    options = project.setdefault("option", {})
    if project.get("pretask") == pretasks and options.get(OPTION_NAME) == settings:
        return False
    project["pretask"] = pretasks
    options[OPTION_NAME] = settings
    temporary = path.with_suffix(".dmm.tmp")
    temporary.write_text(json.dumps(project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", choices=CONTROLLERS)
    parser.add_argument("interface", type=Path)
    args = parser.parse_args()
    prepare(args.game, args.interface)


if __name__ == "__main__":
    main()
