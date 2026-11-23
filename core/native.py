from __future__ import annotations

import json
import sys
from pathlib import Path

from core.config_loader import GameConfig
from core.scheduler import check_game
from games.registry import load_flow
from games.rewards import Outcome
from src.config import open_profile, resolution_for, target_for


def run_native(game_id: str, request: Path) -> bool:
    from src.tasks.DailyClearTask import DailyClearTask

    game = GameConfig(**json.loads(request.read_text(encoding="utf-8")))
    check_game(game_id, game)
    flow = load_flow(game_id)
    app = open_profile(game_id, game)
    try:
        task = app.get_onetime_task(DailyClearTask)
        task.flow = flow
        task.pages = flow.select(game.steps())
        task.platform = game.string("platform")
        task.target = target_for(game)
        task.expected_resolution = resolution_for(game)
        task.adb_serial = game.options.get("adb_serial")
        # ADB 模拟器必须已经连上，框架不应先启动它碰巧发现的实例。
        app.headless_app.start_controller.start_exe = False
        app.run_task(task)
        for result in task.report or ():
            print(f"  {result.step_id}  {result.outcome.value}  {result.detail}", flush=True)
        if task.failure:
            raise RuntimeError(task.failure)
        if task.report is None or len(task.report) != len(task.pages):
            raise RuntimeError("ok-script 没有返回完整的游戏结果，请查看 logs")
        return all(result.outcome != Outcome.FAILED for result in task.report)
    finally:
        app.quit()


if __name__ == "__main__":
    try:
        _, game_id, request_path = sys.argv
        sys.argv = sys.argv[:1]
        sys.exit(0 if run_native(game_id, Path(request_path)) else 1)
    except Exception as exc:
        print(f"内置后端失败：{exc}", file=sys.stderr, flush=True)
        sys.exit(1)
