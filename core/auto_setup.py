from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from uuid import UUID

from core.automas_backend import AUTOMAS_GAMES, AutoMasProfile, discover_automas
from core.config_loader import GameConfig, HubConfig
from core.pcr_setup import discover_pcr

DEFAULT_TOOLS_ROOT = Path.home() / "Games" / "DailyAutomation"


def _profile_for(game: GameConfig, profiles: tuple[AutoMasProfile, ...]) -> AutoMasProfile | None:
    pinned_id = None
    if game.backend == "automas" and isinstance(value := game.options.get("script_id"), str):
        try:
            pinned_id = str(UUID(value))
        except ValueError:
            # 旧示例中的占位文字可直接使用自动发现。
            pass
    if pinned_id is not None:
        profile = next((item for item in profiles if item.script_id == pinned_id), None)
        if profile is None:
            raise ValueError(f"{game.name} 原有 script_id 未匹配可用托管，请更新该绑定")
        return profile
    if len(profiles) > 1:
        labels = "、".join(f"{item.name} ({item.script_id})" for item in profiles)
        raise ValueError(f"{game.name} 有多个托管：{labels}。请保留一个或使用 script_id 指定")
    return profiles[0] if profiles else None


def resolve_automatic(hub: HubConfig, requested: tuple[str, ...], port: int, tools_root: Path) -> HubConfig:
    automas_ids = tuple(game_id for game_id in requested if game_id in AUTOMAS_GAMES)
    profiles = discover_automas(port, automas_ids)
    games = {}
    for game_id in requested:
        game = hub.games[game_id]
        if game_id == "pcr":
            pcr = discover_pcr(game, tools_root)
            if pcr is not None:
                games[game_id] = pcr
            continue
        if profile := _profile_for(game, profiles.get(game_id, ())):
            options = {"script_id": profile.script_id, "automas_port": port, "script_name": profile.name}
            if game.backend == "automas" and "user_id" in game.options:
                options["user_id"] = game.options["user_id"]
            timeout = game.timeout if game.backend == "automas" else 3600
            games[game_id] = replace(game, backend="automas", enabled=True, timeout=timeout, options=options)
    return HubConfig(games, tuple(games))
