from importlib import import_module

from games.rewards import RewardFlow


def load_flow(game_id: str) -> RewardFlow:
    # 游戏 ID 在配置加载时已同内置清单核对。
    return import_module(f"games.{game_id}.flow").DAILY_FLOW
