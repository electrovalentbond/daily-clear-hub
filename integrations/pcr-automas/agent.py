from __future__ import annotations

import json
import os
import subprocess
import sys
import traceback
from contextlib import nullcontext
from datetime import datetime
from functools import partial
from pathlib import Path

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction


INSTALL_CONFIG = Path(__file__).with_name("local.json")
LOG_PATH = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "DailyClearHub" / "pcr-automas.log"
TASK_NODES = (
    "DailyClearPcrSchedule",
    "DailyClearPcrQuestReward",
    "DailyClearPcrGift",
)
NO_ARGUMENT_TASKS = frozenset({
    "schedule", "normal_gacha", "arena", "princess_arena", "research", "adventure_daily",
    "recollection", "dawn_labyrinth", "get_quest_reward", "abyss_subjugation", "team_battle",
    "luna_tower_clean", "luna_tower_climb", "upgrade_all_characters", "claim_alchemy_reward",
    "sweep_revival_hard", "sweep_very_hard_boss",
})
TASK_TIMEOUTS = {
    "campaign_clean": 9000,
    "clear_campaign_first_time": 4200,
    "abyss_subjugation": 8100,
    "team_battle": 4200,
    "luna_tower_climb": 4200,
}
ACTIVITY_TYPES = {"collaboration_raid", "revival", "story"}


def selected_tasks(context, task_rows):
    tasks = []
    for node, task in zip(TASK_NODES, task_rows, strict=True):
        data = context.get_node_data(node)
        attachment = data.get("attach") if isinstance(data, dict) else None
        enabled = attachment.get("enabled") if isinstance(attachment, dict) else None
        if type(enabled) is not bool:
            raise ValueError(f"公主连结任务选项读取失败（{node}）")
        if enabled:
            tasks.append(task)
    if not tasks:
        raise ValueError("请在「日常事项」至少勾选一项")
    return tuple(tasks)


def shop_rules(raw):
    try:
        rules = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError('请填写商店与商品编号，例如 {"1":[1,2]}') from exc
    if not isinstance(rules, dict) or not rules:
        raise ValueError("请先填写要购买的商店与商品编号")
    for shop, items in rules.items():
        if shop not in {"1", "2", "3", "4", "5", "6", "7", "8", "9"} or not isinstance(items, list) or not items:
            raise ValueError("商店购买配置无效，请填写上游支持的商店与商品编号")
        if items == [-1] and shop in {"1", "9"}:
            continue
        if not all(type(item) is int and 1 <= item <= 4 for item in items) or len(set(items)) != len(items):
            raise ValueError("商品编号应为上游支持的首屏 1～4，通常或限定商店可以选择全选")
    return rules


def individual_task(raw):
    task = raw.get("task")
    args = raw.get("args", [])
    settings = raw.get("settings", {})
    if not isinstance(task, str) or not isinstance(args, list) or not isinstance(settings, dict):
        raise ValueError("AUTO-MAS 公主连结任务配置无效")
    if task in {"free_gacha", "get_gift", "clear_campaign_first_time"}:
        valid = len(args) == 1 and type(args[0]) is bool
    elif task == "campaign_clean":
        valid = len(args) == 2 and all(type(value) is bool for value in args)
    elif task == "quick_clean":
        valid = len(args) == 1 and type(args[0]) is int and 1 <= args[0] <= 7
    elif task == "shop_buy":
        valid = len(args) == 1
        if valid:
            args = [shop_rules(args[0])]
    else:
        valid = task in NO_ARGUMENT_TASKS and not args
    if not valid:
        raise ValueError(f"公主连结任务 {task} 的参数无效")

    if task == "campaign_clean":
        options = settings.get("Activities", {})
        activities = options.get("types") if isinstance(options, dict) else None
        if not isinstance(activities, list) or not activities or any(
            not isinstance(activity, str) or activity not in ACTIVITY_TYPES for activity in activities
        ):
            raise ValueError("请至少选择一项活动类型")
        settings = {"Activities": {"types": list(dict.fromkeys(activities))}}
    elif task == "recollection":
        options = settings.get("Recollection", {})
        if not isinstance(options, dict):
            raise ValueError("追忆战场选项无效")
        flags = {key: options.get(key, True) for key in ("claim_rewards", "sweep_dominion")}
        if not all(type(value) is bool for value in flags.values()) or not any(flags.values()):
            raise ValueError("追忆战场至少选择领奖或扫荡一项")
        settings = {"Recollection": flags}
    elif task == "abyss_subjugation":
        settings = {"AbyssSubjugation": {
            "first_clear": False, "auto_equip_special": False, "on_demand_cultivation": False,
        }}
    else:
        settings = {}
    return (task, *args), settings


def launch(context, log, stderr, raw):
    try:
        installation = json.loads(INSTALL_CONFIG.read_text(encoding="utf-8-sig"))
        hub = Path(installation["hub_root"])
        project = Path(installation["pcr_root"])
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise ValueError("无法读取本机安装路径，请重新运行 setup-windows.ps1 -Games pcr 并同步项目") from exc
    if not (
        hub.is_absolute() and (hub / "core" / "pcr_backend.py").is_file()
        and project.is_absolute() and (project / "daily_task.py").is_file()
    ):
        raise ValueError("找不到 Hub 仓库或 pcr-script，请重新运行 setup-windows.ps1 -Games pcr 并同步项目")
    # 安装脚本记录用户机器上的仓库目录。AUTO-MAS 运行的是导入副本。
    sys.path.insert(0, str(hub))
    try:
        from core.config_loader import GameConfig
        from core.pcr_backend import check_pcr, run_pcr
        from core.pcr_setup import PCR_DAILY_TASKS, configure_pcr, find_pcr_target
        from core.scheduler import run_command, run_lock
    finally:
        # core 中使用的导入已经解析，后续不影响 Agent 其它模块的查找。
        sys.path.pop(0)

    if raw:
        task, settings = individual_task(raw)
        tasks = (task,)
        timeout = TASK_TIMEOUTS.get(task[0], 1800)
    else:
        tasks = selected_tasks(context, PCR_DAILY_TASKS)
        settings = {}
        timeout = 1800
    tasker = context.tasker
    info = tasker.controller.info
    if info.get("type") != "adb":
        raise ValueError("公主连结须使用安卓模拟器控制器")
    adb_path = info.get("adb_path")
    serial = info.get("adb_serial")
    if not isinstance(adb_path, str) or not adb_path or not isinstance(serial, str) or not serial:
        raise ValueError("AUTO-MAS 没有提供已绑定模拟器的 ADB 路径和序列号")
    adb = Path(adb_path)
    if not adb.is_absolute() or not adb.is_file():
        raise ValueError(f"找不到 AUTO-MAS 使用的 ADB 程序：{adb}")

    game = configure_pcr(
        GameConfig("公主连结 B 服", True, "pcr_script", timeout, {}), project, adb, serial, tasks, settings=settings,
    )
    with run_lock():
        if find_pcr_target(adb, serial) is None:
            raise ValueError(f"选中的模拟器 {serial} 未连接，或未安装公主连结 B 服")
        check_pcr(game)
        log(f"ADB 设备 {serial} 已就绪，启动 pcr-script")
        run_pcr(
            game, partial(run_command, cancelled=lambda: tasker.stopping, stderr=stderr),
            log=log, individual=bool(raw),
        )


def open_log():
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        return LOG_PATH.open("a", encoding="utf-8", buffering=1)
    except OSError as exc:
        print(f"无法写入公主连结诊断日志 {LOG_PATH}：{exc}", flush=True)
        return nullcontext(None)


@AgentServer.custom_action("DailyClearPcr")
class DailyClearPcr(CustomAction):
    def run(self, context, argv):
        with open_log() as stream:
            def log(message):
                print(message, flush=True)
                if stream is not None:
                    try:
                        stream.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}\n")
                    except OSError as exc:
                        print(f"写入公主连结诊断日志失败：{exc}", flush=True)

            log("开始公主连结日常")
            try:
                raw = json.loads(getattr(argv, "custom_action_param", "") or "null")
                if raw is not None and not isinstance(raw, dict):
                    raise ValueError("AUTO-MAS 公主连结任务参数应为对象")
                launch(context, log, stream, raw)
            except subprocess.TimeoutExpired:
                log("公主连结运行或设备连接超时")
                return False
            except (ImportError, OSError, RuntimeError, ValueError) as exc:
                log(f"公主连结运行失败：{exc}")
                return False
            except Exception:
                log(f"公主连结接入异常：\n{traceback.format_exc()}")
                return False
            log("公主连结日常完成")
            return True


if __name__ == "__main__":
    if len(sys.argv) < 2 or not AgentServer.start_up(sys.argv[-1]):
        raise SystemExit("公主连结 Agent 无法启动，请从 AUTO-MAS 运行托管")
    try:
        AgentServer.join()
    finally:
        AgentServer.shut_down()
