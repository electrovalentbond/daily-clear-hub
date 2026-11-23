from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml

from core.config_loader import DEFAULT_LOCAL_CONFIG_PATH, PROJECT_ROOT, load_hub_config
from core.scheduler import RunAborted, check_game, run_lock, run_queue
from games.registry import load_flow


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Daily Clear Hub · 多游戏日常")
    parser.add_argument("--config", type=Path, default=DEFAULT_LOCAL_CONFIG_PATH, help="本机 YAML 覆盖文件")
    commands = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("plan", "查看游戏和步骤，不连接游戏"),
        ("check", "检查已选游戏的本机配置与素材"),
        ("run", "按顺序执行日常"),
    ):
        subparser = commands.add_parser(command, help=help_text)
        subparser.add_argument("games", nargs="*", metavar="GAME", help="游戏 ID（可显式选择未启用的游戏）")
        if command == "plan":
            subparser.add_argument("--features", action="store_true", help="列出所选内置步骤需要的模板")
    gui = commands.add_parser("gui", help="打开指定游戏的 ok-script 截图与诊断工具")
    gui.add_argument("games", nargs=1, metavar="GAME")
    gui.add_argument("--debug", action="store_true", help="打开 ok-script 调试功能")
    args = parser.parse_args(argv)
    config_path = args.config.resolve()

    try:
        hub = load_hub_config(config_path)
        selected = hub.select(args.games, include_disabled=args.command == "plan")
        if not selected:
            raise ValueError("没有选中游戏。请在本机配置中启用游戏，或在命令后指定游戏 ID")
        if args.command == "plan":
            for game_id in selected:
                game = hub.games[game_id]
                status = "已启用" if game.enabled else "未启用"
                print(f"[{game_id}] {game.name} · {status} · {game.backend}")
                if game.backend == "native":
                    flow = load_flow(game_id)
                    chosen = flow.select(game.steps())
                    for page in chosen:
                        print(f"  [✓] {page.step_id} · {page.name}")
                    for page in flow.pages:
                        if page not in chosen:
                            print(f"  [ ] {page.step_id} · {page.name}")
                    if args.features:
                        for feature in sorted(flow.required_features(chosen)):
                            print(f"      {feature}")
                else:
                    print("  使用上游工具的本机日常配置")
            return 0
        if args.command == "check":
            success = True
            for game_id in selected:
                try:
                    check_game(game_id, hub.games[game_id])
                except (ValueError, OSError) as exc:
                    print(f"[{game_id}] {exc}", file=sys.stderr)
                    success = False
                else:
                    print(f"[{game_id}] 静态配置检查通过")
            return 0 if success else 1
        if os.name != "nt":
            raise ValueError("运行与截图诊断需要 Windows")
        with run_lock():
            if args.command == "run":
                return 0 if run_queue(hub, selected) else 1
            from src.config import open_profile

            game_id = selected[0]
            diagnostics = PROJECT_ROOT / "configs" / game_id / "diagnostics"
            diagnostics.mkdir(parents=True, exist_ok=True)
            os.chdir(diagnostics)
            # ok-script 自行解析 argv；移除 Hub 专用参数。
            sys.argv = sys.argv[:1]
            open_profile(game_id, hub.games[game_id], gui=True, debug=args.debug).start()
            return 0
    except KeyboardInterrupt:
        print("已取消", file=sys.stderr)
        return 130
    except (ValueError, OSError, ImportError, RunAborted, yaml.YAMLError) as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
