from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"
DEFAULT_LOCAL_CONFIG_PATH = PROJECT_ROOT / "config.local.yaml"


@dataclass
class SchedulerConfig:
    task_timeout_sec: int = 1800
    max_retries: int = 2
    retry_delay_sec: int = 10


@dataclass
class GameConfig:
    enabled: bool = False
    platform: str = "windows"
    tasks: list[str] = field(default_factory=list)
    emulator_index: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class HubConfig:
    schedule_order: list[str] = field(default_factory=list)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    games: dict[str, GameConfig] = field(default_factory=dict)
    windows: dict[str, str] = field(default_factory=dict)
    emulator: dict[str, str] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _parse_game_config(game_id: str, data: dict[str, Any]) -> GameConfig:
    known_keys = {"enabled", "platform", "tasks", "emulator_index"}
    extra = {key: value for key, value in data.items() if key not in known_keys}
    return GameConfig(
        enabled=bool(data.get("enabled", False)),
        platform=str(data.get("platform", "windows")),
        tasks=list(data.get("tasks", [])),
        emulator_index=int(data.get("emulator_index", 0)),
        extra=extra,
    )


def load_hub_config(
    config_path: Path | None = None,
    local_config_path: Path | None = None,
) -> HubConfig:
    config_path = config_path or DEFAULT_CONFIG_PATH
    local_config_path = local_config_path or DEFAULT_LOCAL_CONFIG_PATH

    with config_path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if local_config_path.exists():
        with local_config_path.open(encoding="utf-8") as handle:
            local_data = yaml.safe_load(handle) or {}
        data = _deep_merge(data, local_data)

    scheduler_data = data.get("scheduler", {})
    scheduler = SchedulerConfig(
        task_timeout_sec=int(scheduler_data.get("task_timeout_sec", 1800)),
        max_retries=int(scheduler_data.get("max_retries", 2)),
        retry_delay_sec=int(scheduler_data.get("retry_delay_sec", 10)),
    )

    games = {
        game_id: _parse_game_config(game_id, game_data)
        for game_id, game_data in (data.get("games") or {}).items()
    }

    return HubConfig(
        schedule_order=list(data.get("schedule_order", [])),
        scheduler=scheduler,
        games=games,
        windows=dict(data.get("windows") or {}),
        emulator=dict(data.get("emulator") or {}),
        raw=data,
    )


def enabled_games_in_order(hub_config: HubConfig) -> list[tuple[str, GameConfig]]:
    ordered: list[tuple[str, GameConfig]] = []
    seen: set[str] = set()

    for game_id in hub_config.schedule_order:
        game = hub_config.games.get(game_id)
        if game and game.enabled:
            ordered.append((game_id, game))
            seen.add(game_id)

    for game_id, game in hub_config.games.items():
        if game.enabled and game_id not in seen:
            ordered.append((game_id, game))

    return ordered
