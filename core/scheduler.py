from __future__ import annotations

import ctypes
import json
import os
import signal
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

from core.config_loader import PROJECT_ROOT, GameConfig, HubConfig
from core.templates import check_templates
from games.registry import load_flow
from src.config import resolution_for, target_for


def executable_for(game: GameConfig) -> Path:
    executable = game.path("executable")
    if executable.suffix.lower() != ".exe" or not executable.is_file():
        raise ValueError(f"找不到 Windows 可执行文件：{executable}")
    return executable


def check_game(game_id: str, game: GameConfig) -> None:
    if game.backend == "march7th":
        if game_id != "starrail":
            raise ValueError("march7th 后端仅支持 starrail")
        if executable_for(game).name.casefold() != "m7a.exe":
            raise ValueError("请将 executable 指向三月七小助手的 m7a.exe")
        return
    if game.backend == "hka":
        if game_id != "bhxy2":
            raise ValueError("hka 后端仅支持 bhxy2")
        from core.hka_backend import check_hka

        check_hka(game)
        return
    flow = load_flow(game_id)
    pages = flow.select(game.steps())
    target_for(game)
    resolution_for(game)
    check_templates(game.path("templates"), flow.required_features(pages))


class RunAborted(RuntimeError):
    """停止队列，因为子进程的退出状态无法确认。"""


@contextmanager
def run_lock():
    path = PROJECT_ROOT / "configs" / "hub.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle:
        try:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ValueError("已有 Daily Clear Hub 队列或诊断窗口在运行") from exc
        yield


def _stop_process(process: subprocess.Popen) -> None:
    if os.name == "nt":
        result = subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            timeout=15,
        )
        if result.returncode and process.poll() is None:
            raise RunAborted(f"无法终止任务进程 {process.pid}，队列已停止")
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired as exc:
        raise RunAborted(f"任务进程 {process.pid} 仍在运行，队列已停止") from exc


def run_command(command: list[str], cwd: Path, timeout: int, *, stdout=None) -> int:
    kwargs = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.DEVNULL, stdout=stdout, **kwargs)
    try:
        return process.wait(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        try:
            _stop_process(process)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RunAborted(f"无法确认任务进程 {process.pid} 已停止，队列已停止") from exc
        raise


def _run_march7th(game: GameConfig) -> None:
    if os.name != "nt" or not ctypes.windll.shell32.IsUserAnAdmin():
        raise ValueError("三月七小助手需要从管理员 PowerShell 运行，以便 Hub 等待同一进程")
    executable = executable_for(game)
    command = [str(executable), "routine", "--non-interactive", "--after-finish", "None"]
    code = run_command(command, executable.parent, game.timeout)
    if code:
        raise ValueError(f"三月七小助手退出码 {code}，请查看其日志")


def _run_native(game_id: str, game: GameConfig) -> None:
    with TemporaryDirectory(prefix="daily-clear-") as folder:
        request = Path(folder) / "game.json"
        request.write_text(json.dumps(asdict(game), ensure_ascii=False), encoding="utf-8")
        command = [sys.executable, "-u", "-m", "core.native", game_id, str(request)]
        if run_command(command, PROJECT_ROOT, game.timeout):
            raise ValueError("内置后端有步骤失败或未完成")


def run_queue(hub: HubConfig, game_ids: tuple[str, ...]) -> bool:
    all_succeeded = True
    for game_id in game_ids:
        game = hub.games[game_id]
        print(f"\n[{game_id}] {game.name} · {game.backend}", flush=True)
        try:
            check_game(game_id, game)
            if game.backend == "march7th":
                _run_march7th(game)
            elif game.backend == "hka":
                from core.hka_backend import run_hka

                run_hka(game, run_command)
            else:
                _run_native(game_id, game)
            print(f"[{game_id}] 完成", flush=True)
        except subprocess.TimeoutExpired:
            if game.backend != "native":
                raise RunAborted(f"[{game_id}] 超过 {game.timeout} 秒，队列已停止。请确认上游任务结束后再运行") from None
            print(f"[{game_id}] 超过 {game.timeout} 秒，已终止任务进程", file=sys.stderr, flush=True)
            all_succeeded = False
        except (ValueError, OSError) as exc:
            print(f"[{game_id}] {exc}", file=sys.stderr, flush=True)
            all_succeeded = False
    return all_succeeded
