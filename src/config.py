from __future__ import annotations

import logging

from core.config_loader import PROJECT_ROOT, GameConfig

version = "dev"


def resolution_for(game: GameConfig) -> tuple[int, int]:
    resolution = game.options.get("resolution")
    if (
        not isinstance(resolution, list) or len(resolution) != 2
        or not all(type(size) is int and size > 0 for size in resolution)
    ):
        raise ValueError("resolution 应为 [宽, 高]，使用正整数")
    return tuple(resolution)


def target_for(game: GameConfig) -> str:
    platform = game.string("platform")
    if platform == "windows":
        exe = game.string("exe")
        if "/" in exe or "\\" in exe or not exe.lower().endswith(".exe"):
            raise ValueError("exe 应为游戏进程名，例如 StarRail.exe")
        interaction = game.options.get("interaction", "Pynput")
        if interaction not in ("Pynput", "PyDirect", "PostMessage", "ForegroundPostMessage", "Genshin"):
            raise ValueError("interaction 不是支持的 Windows 输入方式")
        return exe
    if platform == "adb":
        game.string("adb_serial")
        return game.string("package")
    raise ValueError(f"未知平台：{platform}")


def make_profile(game_id: str, game: GameConfig, *, gui: bool = False, debug: bool = False) -> dict:
    width, height = resolution_for(game)
    target = target_for(game)
    templates = game.path("templates")
    profile = {
        "version": version,
        "use_gui": gui,
        "debug": debug,
        "check_mutex": False,
        "custom_tasks": False,
        "config_folder": str(PROJECT_ROOT / "configs" / game_id),
        "gui_title": f"Daily Clear Hub · {game.name}",
        "gui_icon": str(PROJECT_ROOT / "icons" / "icon.png"),
        "wait_until_settle_time": 0,
        "start_timeout": 20,
        "supported_resolution": {"ratio": f"{width}:{height}", "min_size": (width, height)},
        "onetime_tasks": [["ok", "DiagnosisTask"]] if gui else [],
        "screenshots_folder": str(PROJECT_ROOT / "screenshots" / game_id),
    }
    if templates.is_file():
        profile["template_matching"] = {"coco_feature_json": str(templates), "default_threshold": 0.85}
    if game.string("platform") == "windows":
        profile["windows"] = {
            "exe": [target],
            "start_exe": False,
            "interaction": [game.options.get("interaction", "Pynput")],
            "capture_method": ["WGC", "BitBlt_RenderFull", "BitBlt"],
        }
    else:
        # 保持包列表为空，避免框架自动打开选中设备上的应用。
        # 运行任务前会另外核对设备序列号和前台包名。
        profile["adb"] = {"packages": []}
    return profile


def open_profile(game_id: str, game: GameConfig, *, gui: bool = False, debug: bool = False):
    from ok import OK

    def filter_environment(record: logging.LogRecord) -> bool:
        return not record.getMessage().startswith("ok:env ")

    # 1.0.154 会在启动时记录所有环境变量值。
    logger = logging.getLogger("ok")
    logger.addFilter(filter_environment)
    try:
        return OK(make_profile(game_id, game, gui=gui, debug=debug))
    finally:
        logger.removeFilter(filter_environment)
