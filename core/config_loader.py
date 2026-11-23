from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"
DEFAULT_LOCAL_CONFIG_PATH = PROJECT_ROOT / "config.local.yaml"


@dataclass(frozen=True)
class GameConfig:
    name: str
    enabled: bool
    backend: str
    timeout: int
    options: dict[str, Any]

    def string(self, key: str) -> str:
        value = self.options.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"请设置 {key}")
        return value.strip()

    def path(self, key: str) -> Path:
        return (PROJECT_ROOT / self.string(key)).resolve()

    def steps(self) -> tuple[str, ...]:
        steps = self.options.get("steps")
        if not isinstance(steps, list) or not steps or not all(isinstance(step, str) for step in steps):
            raise ValueError("steps 应为非空的步骤 ID 列表")
        if len(steps) != len(set(steps)):
            raise ValueError("steps 中有重复的步骤 ID")
        return tuple(steps)


@dataclass(frozen=True)
class HubConfig:
    games: dict[str, GameConfig]
    order: tuple[str, ...]

    def select(self, game_ids: list[str], *, include_disabled: bool = False) -> tuple[str, ...]:
        unknown = set(game_ids) - self.games.keys()
        if unknown:
            raise ValueError(f"未知游戏 ID：{', '.join(sorted(unknown))}")
        if game_ids:
            return tuple(dict.fromkeys(game_ids))
        return tuple(game_id for game_id in self.order if include_disabled or self.games[game_id].enabled)


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as handle:
        data = yaml.safe_load(handle)
    if data is None:
        return {}
    if not isinstance(data, dict) or not all(isinstance(key, str) for key in data):
        raise ValueError(f"{path.name} 须为使用文本键名的 YAML 映射")
    return data


def load_hub_config(local_config_path: Path = DEFAULT_LOCAL_CONFIG_PATH) -> HubConfig:
    defaults = _load_yaml(DEFAULT_CONFIG_PATH)
    overrides = _load_yaml(local_config_path) if local_config_path.exists() else {}
    extra = overrides.keys() - {"schedule_order", "games"}
    if extra:
        raise ValueError(f"未知配置项：{', '.join(sorted(extra))}。请参考 config.local.yaml.example")

    game_overrides = overrides.get("games", {})
    if not isinstance(game_overrides, dict) or not all(isinstance(key, str) for key in game_overrides):
        raise ValueError("games 须为 YAML 映射")
    game_defaults = defaults["games"]
    unknown = game_overrides.keys() - game_defaults.keys()
    if unknown:
        raise ValueError(f"games 含未知游戏：{', '.join(sorted(unknown))}")

    games = {}
    for game_id, config in game_defaults.items():
        override = game_overrides.get(game_id, {})
        if not isinstance(override, dict) or not all(isinstance(key, str) for key in override):
            raise ValueError(f"games.{game_id} 须为 YAML 映射")
        extra = override.keys() - config.keys() - {"interaction", "executable", "hka_config", "project_dir"}
        if extra:
            raise ValueError(f"games.{game_id} 有未知配置项：{', '.join(sorted(extra))}")
        options = {**config, **override}
        enabled = options.pop("enabled")
        backend = options.pop("backend")
        timeout = options.pop("timeout_sec")
        if type(enabled) is not bool:
            raise ValueError(f"games.{game_id}.enabled 应为 true 或 false")
        if not isinstance(backend, str) or backend not in ("native", "march7th", "hka"):
            raise ValueError(f"games.{game_id}.backend 未知：{backend}")
        if type(timeout) is not int or timeout <= 0:
            raise ValueError(f"games.{game_id}.timeout_sec 应为正整数")
        games[game_id] = GameConfig(options.pop("name"), enabled, backend, timeout, options)

    order = overrides.get("schedule_order", defaults["schedule_order"])
    if not isinstance(order, list) or not all(isinstance(game_id, str) for game_id in order):
        raise ValueError("schedule_order 须为游戏 ID 列表")
    if set(order) - games.keys() or len(order) != len(set(order)):
        raise ValueError("schedule_order 含未知或重复的游戏 ID")
    return HubConfig(games, tuple(dict.fromkeys([*order, *games])))
