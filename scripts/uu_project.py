"""Add the selectable UU pretask to a copy of a MaaFW project."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

if __package__:
    from .dmm_project import CONTROLLERS
    from .uu_boost import main as boost
else:
    from dmm_project import CONTROLLERS
    from uu_boost import main as boost


TASK_NAME = "DailyClearHubUuBoost"
OPTION_NAME = "DailyClearHubUuSettings"
LAUNCH_OPTION = "DailyClearHubUuLaunchGame"
OPTIONS_ENV = "DAILY_CLEAR_HUB_UU_OPTIONS"
PROJECTS = {
    "gakumas": ("DailyClearHubUuGakumas", "学园偶像大师（含 UU）"),
    "dotabyss": ("DailyClearHubUuDotAbyss", "Dot Abyss（含 UU）"),
}


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def prepare(game: str, source: Path, destination: Path, python: Path, runner: Path) -> None:
    if source.resolve() == destination.resolve():
        raise ValueError("UU pretask must be added to a separate project copy")
    interface = json.loads(source.read_text(encoding="utf-8-sig"))
    interface["name"], interface["label"] = PROJECTS[game]
    # The local project has a different task list and must have its own AUTO-MAS payload.
    for field in ("github", "mirrorchyan_rid", "mirrorchyanRid"):
        interface.pop(field, None)
    pretasks = interface.get("pretask") or []
    if isinstance(pretasks, dict):
        pretasks = [pretasks]
    interface["pretask"] = [
        {
            "name": TASK_NAME,
            "label": "切换网易 UU 加速",
            "description": "确认所填游戏已加速，可选在 UU 内启动 DMM 游戏。请输入 UU 界面显示的完整名称。",
            "exec": "powershell",
            "args": [
                "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                "-File", "{PROJECT_DIR}/daily-clear-uu.ps1", "-DmmGame", game,
            ],
            "option": [OPTION_NAME, LAUNCH_OPTION],
        },
        *(task for task in pretasks if task.get("name") != TASK_NAME),
    ]
    options = interface.setdefault("option", {})
    options[OPTION_NAME] = {
        "type": "input",
        "label": "UU 加速设置",
        "inputs": [
            {"name": "game", "label": "UU 中的游戏全名", "default": ""},
            {"name": "region", "label": "区服选项（可留空）", "default": ""},
            {"name": "exe", "label": "UU 程序路径（可留空）", "default": ""},
        ],
    }
    options[LAUNCH_OPTION] = {
        "type": "switch",
        "label": "UU 加速后启动 DMM 游戏",
        "description": "点击 UU 的「启动游戏」，等游戏窗口出现后再交给 AUTO-MAS。使用单独的 DMM 快捷方式前置任务时选「否」。",
        "controller": [CONTROLLERS[game]],
        "default_case": "Yes",
        "cases": [{"name": "Yes", "label": "是"}, {"name": "No", "label": "否"}],
    }
    write_json(destination.with_name("daily-clear-uu.json"), {"python": str(python), "runner": str(runner)})
    write_json(destination, interface)


def boost_arguments(raw_options: str) -> list[str]:
    options = json.loads(raw_options)
    settings = options.get(OPTION_NAME) if isinstance(options, dict) else None
    if not isinstance(settings, dict):
        raise ValueError("请在「切换网易 UU 加速」里填写 UU 中的游戏全名")
    game = settings.get("game", "")
    if not isinstance(game, str) or not game.strip():
        raise ValueError("请在「切换网易 UU 加速」里填写 UU 中的游戏全名")
    arguments = [f"--game={game.strip()}"]
    for field in ("region", "exe"):
        value = settings.get(field, "")
        if isinstance(value, str) and value.strip():
            arguments.append(f"--{field}={value.strip()}")
    if options.get(LAUNCH_OPTION) == "Yes":
        arguments.append("--launch-game")
    return arguments


def run_pretask(options: list[str], game: str | None, project_dir: Path) -> int:
    launch = "--launch-game" in options
    if launch and not game:
        raise ValueError("缺少 DMM 游戏启动配置，请重跑带 -WithUu 的安装命令并同步托管")
    mode = "加速后从 UU 启动 DMM 游戏" if launch else "仅加速"
    print(f"UU 本次模式：{mode}", flush=True)
    result = boost(options)
    if result or not launch:
        return result
    return subprocess.run([
        "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
        "-File", str(project_dir / "daily-clear-dmm.ps1"), "-Game", game, "-WaitOnly",
    ], check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    install = subcommands.add_parser("prepare")
    install.add_argument("game", choices=PROJECTS)
    install.add_argument("source", type=Path)
    install.add_argument("destination", type=Path)
    install.add_argument("python", type=Path)
    install.add_argument("runner", type=Path)
    pretask = subcommands.add_parser("pretask")
    pretask.add_argument("--dmm-game", choices=PROJECTS)
    pretask.add_argument("--project-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.game, args.source, args.destination, args.python, args.runner)
        return 0
    try:
        options = boost_arguments(os.environ.get(OPTIONS_ENV) or "{}")
        return run_pretask(options, args.dmm_game, args.project_dir)
    except (OSError, ValueError, TypeError) as exc:
        print(f"UU 前置任务失败：{exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
