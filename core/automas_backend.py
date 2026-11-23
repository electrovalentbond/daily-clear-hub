from __future__ import annotations

import http.client
import json
import re
import time
from dataclasses import dataclass
from uuid import UUID

from core.config_loader import GameConfig
from core.errors import RunAborted

DEFAULT_PORT = 36163
_SPECIALIZED_GAMES = {
    "HSRConfig": "starrail",
    "MaaEndConfig": "endfield",
    "BetterGIConfig": "genshin",
    "ZzzOdConfig": "zzz",
}
_MAA_PROJECTS = {
    "honkai3": "https://github.com/miaojiuqing/maa_bbb",
    "endfield": "https://github.com/maaend/maaend",
    "bhxy2": "https://github.com/freeze-12/maabh2",
}
AUTOMAS_GAMES = frozenset((*_SPECIALIZED_GAMES.values(), *_MAA_PROJECTS))
_ACCOUNT_TOTALS = re.compile(r"^ {4}已完成账号数：([0-9]+)；未完成账号数：([0-9]+)$", re.MULTILINE)
_MAX_RESPONSE = 4 * 1024 * 1024


class _ApiUnavailable(ValueError):
    pass


@dataclass(frozen=True)
class AutoMasProfile:
    script_id: str
    name: str


def _uuid(value: object, field: str) -> str:
    if isinstance(value, str):
        try:
            return str(UUID(value))
        except ValueError:
            pass
    raise ValueError(f"AUTO-MAS {field} 应为 UUID")


def _validate_port(port: object) -> int:
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("automas_port 应为 1 到 65535 的整数")
    return port


def _port(game: GameConfig) -> int:
    return _validate_port(game.options.get("automas_port", DEFAULT_PORT))


def _request(port: int, path: str, payload: dict | None = None, *, timeout: float = 5) -> dict:
    # 只连接本机 API。HTTPConnection 不会使用代理或自动跟随重定向。
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    try:
        connection.request("GET" if payload is None else "POST", path, body=body, headers=headers)
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError(f"AUTO-MAS {path} 返回 HTTP {response.status}")
        content = response.read(_MAX_RESPONSE + 1)
        if len(content) > _MAX_RESPONSE:
            raise ValueError(f"AUTO-MAS {path} 响应过长")
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError(f"AUTO-MAS {path} 返回了无法识别的数据")
        return data
    except (http.client.HTTPException, OSError) as exc:
        raise _ApiUnavailable(f"无法连接 AUTO-MAS {path}。请确认本机程序已启动，端口为 {port}") from exc
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"AUTO-MAS {path} 未返回有效的 JSON") from exc
    finally:
        connection.close()


def _check_success(data: dict, action: str) -> None:
    if data.get("code") != 200 or data.get("status") != "success":
        message = data.get("message") or "上游返回错误"
        raise ValueError(f"AUTO-MAS {action}：{message}")


def _check_health(port: int) -> None:
    health = _request(port, "/api/core/health")
    if health.get("ready") is not True or health.get("protocol") != 1:
        raise ValueError("AUTO-MAS 尚未就绪或接口版本不兼容，请参照 Windows 手册")


def _maa_repository(port: int, script_id: str) -> str | None:
    response = _request(port, "/api/scripts/maafw/preview", {"scriptId": script_id})
    _check_success(response, "检查 MFW 资源")
    data = response.get("data")
    project = data.get("project") if isinstance(data, dict) else None
    repository = project.get("github") if isinstance(project, dict) else None
    return repository.rstrip("/").casefold() if isinstance(repository, str) else None


def discover_automas(port: int, game_ids: tuple[str, ...]) -> dict[str, tuple[AutoMasProfile, ...]]:
    """从既有托管识别支持的游戏，名称只用于显示。"""
    if not game_ids:
        return {}
    _validate_port(port)
    _check_health(port)
    scripts = _request(port, "/api/scripts/get", {})
    _check_success(scripts, "读取托管列表")
    index = scripts.get("index")
    data = scripts.get("data")
    if not isinstance(index, list) or not isinstance(data, dict) or any(not isinstance(row, dict) for row in index):
        raise ValueError("AUTO-MAS 返回的托管列表格式不兼容")

    profiles: dict[str, list[AutoMasProfile]] = {game_id: [] for game_id in game_ids}
    repositories = {repository: game_id for game_id, repository in _MAA_PROJECTS.items() if game_id in profiles}
    for row in index:
        script_type = row.get("type")
        if not isinstance(script_type, str):
            raise ValueError("AUTO-MAS 返回的托管类型无效")
        game_id = _SPECIALIZED_GAMES.get(script_type)
        if script_type == "MaaFWConfig" and repositories:
            script_id = _uuid(row.get("uid"), "托管 ID")
            try:
                game_id = repositories.get(_maa_repository(port, script_id))
            except _ApiUnavailable:
                raise
            except ValueError:
                # 未完成资源配置的托管暂时无法确认所属游戏。
                continue
        if game_id not in profiles:
            continue
        script_id = _uuid(row.get("uid"), "托管 ID")
        script = data.get(script_id)
        info = script.get("Info") if isinstance(script, dict) else None
        name = info.get("Name") if isinstance(info, dict) else None
        profiles[game_id].append(AutoMasProfile(script_id, name if isinstance(name, str) and name else script_id))
    return {game_id: tuple(matched) for game_id, matched in profiles.items()}


def check_automas(game_id: str, game: GameConfig) -> None:
    if game_id not in AUTOMAS_GAMES:
        raise ValueError(f"AUTO-MAS 后端不支持 {game_id}")
    port = _port(game)
    script_id = _uuid(game.options.get("script_id"), "script_id")
    user_id = _uuid(game.options["user_id"], "user_id") if "user_id" in game.options else None

    _check_health(port)
    scripts = _request(port, "/api/scripts/get", {"scriptId": script_id})
    _check_success(scripts, "检查托管")
    index = scripts.get("index")
    if not (
        isinstance(index, list) and len(index) == 1
        and isinstance(index[0], dict) and index[0].get("uid") == script_id
    ):
        raise ValueError(f"AUTO-MAS 未返回指定托管 {script_id}")

    script_type = index[0].get("type")
    if script_type == "MaaFWConfig" and game_id in _MAA_PROJECTS:
        if _maa_repository(port, script_id) != _MAA_PROJECTS[game_id]:
            raise ValueError(f"AUTO-MAS 托管 {script_id} 未使用 {game.name} 的上游项目")
    elif not isinstance(script_type, str) or _SPECIALIZED_GAMES.get(script_type) != game_id:
        expected = [name for name, target in _SPECIALIZED_GAMES.items() if target == game_id]
        if game_id in _MAA_PROJECTS:
            expected.append("MaaFWConfig")
        raise ValueError(f"AUTO-MAS 托管 {script_id} 应使用 {'或'.join(expected)}")

    if user_id is not None:
        response = _request(port, "/api/scripts/user/get", {"scriptId": script_id, "userId": user_id})
        _check_success(response, "检查账号")
        users = response.get("data")
        user = users.get(user_id) if isinstance(users, dict) else None
        info = user.get("Info") if isinstance(user, dict) else None
        if not isinstance(info, dict) or info.get("Status") is not True or info.get("RemainedDay") == 0:
            raise ValueError(f"AUTO-MAS 托管 {script_id} 的指定账号未启用或不可运行")


def _task_result(port: int, task_id: str, script_id: str, user_id: str | None, timeout: float) -> dict:
    result = _request(port, f"/api/dispatch/task/{task_id}", timeout=timeout)
    if (
        result.get("code") != 200 or result.get("taskId") != task_id
        or result.get("scriptId") != script_id or result.get("userId") != user_id
        or result.get("mode") != "AutoProxy" or result.get("queueId") is not None
    ):
        raise ValueError("上游未返回本次托管任务的状态")
    return result


def _wait_for_task(port: int, task_id: str, script_id: str, user_id: str | None, timeout: int) -> dict:
    deadline = time.monotonic() + timeout
    consecutive_errors = 0
    while (remaining := deadline - time.monotonic()) > 0:
        try:
            result = _task_result(port, task_id, script_id, user_id, min(remaining, 5))
        except _ApiUnavailable:
            consecutive_errors += 1
            if consecutive_errors > 2:
                raise
        else:
            consecutive_errors = 0
            status = result.get("status")
            if status in ("success", "error", "cancelled") and result.get("finishedAt"):
                return result
            if status != "running":
                raise ValueError("上游返回了无法验证的运行状态")
        time.sleep(min(1, max(0, deadline - time.monotonic())))
    raise ValueError(f"超过 {timeout} 秒未取得终态")


def _snapshot_task_ids(port: int) -> set[str]:
    tasks = _request(port, "/api/dispatch/runtime-snapshot").get("tasks")
    if not isinstance(tasks, list) or any(not isinstance(task, dict) for task in tasks):
        raise ValueError("AUTO-MAS 未返回可识别的运行任务列表")
    return {_uuid(task.get("taskId"), "运行任务 ID") for task in tasks}


def _wait_for_cleanup(port: int, task_id: str) -> None:
    # v5.8.0 先发布终态，再从活动列表移除并解锁托管。
    deadline = time.monotonic() + 10
    while tasks := _snapshot_task_ids(port):
        if tasks != {task_id}:
            raise ValueError("AUTO-MAS 启动了其他任务")
        if time.monotonic() >= deadline:
            raise ValueError("已收到终态，但上游尚未释放任务")
        time.sleep(0.25)


def _check_task_result(task_id: str, result: dict, user_id: str | None) -> None:
    if result.get("status") != "success":
        raise ValueError(f"AUTO-MAS 任务 {task_id} 结束，状态 {result.get('status')}")
    detail = result.get("detail")
    totals = _ACCOUNT_TOTALS.findall(detail) if isinstance(detail, str) else []
    if len(totals) != 1:
        raise ValueError(f"AUTO-MAS 任务 {task_id} 的报告未确认账号完成，请在调度台查阅")
    completed, incomplete = map(int, totals[0])
    if incomplete or not completed or (user_id is not None and completed != 1):
        raise ValueError(f"AUTO-MAS 任务 {task_id} 已完成账号 {completed}，未完成 {incomplete}")
    print(f"AUTO-MAS 任务 {task_id} 确认完成 {completed} 个账号", flush=True)


def _request_stop(port: int, task_id: str, script_id: str, user_id: str | None) -> str:
    try:
        task = _task_result(port, task_id, script_id, user_id, timeout=3)
        status = task.get("status")
        if status in ("success", "error", "cancelled") and task.get("finishedAt"):
            return "上游已返回终态"
        if status != "running":
            raise ValueError("上游未返回可停止的运行状态")
        result = _request(port, "/api/dispatch/stop", {"taskId": task_id}, timeout=3)
        _check_success(result, "请求停止")
    except ValueError:
        return "未收到停止确认"
    return "已请求停止"


def run_automas(game_id: str, game: GameConfig) -> None:
    # 调度器已调用 check_automas 核对托管 ID 和游戏来源。
    if game_id not in AUTOMAS_GAMES:
        raise ValueError(f"AUTO-MAS 后端不支持 {game_id}")
    port = _port(game)
    script_id = _uuid(game.options.get("script_id"), "script_id")
    user_id = _uuid(game.options["user_id"], "user_id") if "user_id" in game.options else None
    if _snapshot_task_ids(port):
        raise RunAborted("AUTO-MAS 有运行中的任务，Hub 队列已停止")
    power = _request(port, "/api/dispatch/get/power", {})
    if power.get("code") != 200 or power.get("signal") != "NoAction":
        raise RunAborted("AUTO-MAS 有待执行的电源操作或状态未知，Hub 队列已停止")

    task_id = None
    try:
        start = {"taskId": script_id, "mode": "AutoProxy"}
        if user_id is not None:
            start["userId"] = user_id
        reply = _request(port, "/api/dispatch/start", start)
        _check_success(reply, "提交任务")
        task_id = _uuid(reply.get("taskId"), "任务 ID")
        if task_id == script_id:
            task_id = None
            raise ValueError("上游没有返回独立的运行 ID")
        print(f"AUTO-MAS 已接收任务 {task_id}，可在其调度台查看进度", flush=True)
        result = _wait_for_task(port, task_id, script_id, user_id, game.timeout)
        _wait_for_cleanup(port, task_id)
    except (KeyboardInterrupt, ValueError) as exc:
        if task_id is None:
            raise RunAborted("AUTO-MAS 未确认本次任务是否启动。Hub 队列已停止，请先查看调度台") from exc
        stop_result = _request_stop(port, task_id, script_id, user_id)
        reason = "已取消" if isinstance(exc, KeyboardInterrupt) else str(exc)
        raise RunAborted(f"AUTO-MAS 任务 {task_id} {stop_result}（{reason}）。Hub 队列已停止，请确认上游结束") from exc

    _check_task_result(task_id, result, user_id)
