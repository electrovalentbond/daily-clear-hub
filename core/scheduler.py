from __future__ import annotations

import ctypes
import json
import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

from core.automas_backend import check_automas, run_automas
from core.config_loader import PROJECT_ROOT, UPSTREAM_BACKENDS, GameConfig, HubConfig
from core.errors import RunAborted
from core.hka_backend import check_hka, run_hka
from core.pcr_backend import check_pcr, run_pcr
from core.templates import check_templates
from games.registry import load_flow
from src.config import resolution_for, target_for

_COMMAND_BACKENDS = {
    "hka": (check_hka, run_hka),
    "pcr_script": (check_pcr, run_pcr),
}


def executable_for(game: GameConfig) -> Path:
    executable = game.path("executable")
    if executable.suffix.lower() != ".exe" or not executable.is_file():
        raise ValueError(f"找不到 Windows 可执行文件：{executable}")
    return executable


def check_game(game_id: str, game: GameConfig) -> None:
    if game.backend != "native" and game.backend not in UPSTREAM_BACKENDS.get(game_id, ()):
        raise ValueError(f"{game.backend} 后端不适用于 {game_id}")
    if game.backend == "march7th":
        if executable_for(game).name.casefold() != "m7a.exe":
            raise ValueError("请将 executable 指向三月七小助手的 m7a.exe")
        return
    if game.backend == "automas":
        check_automas(game_id, game)
        return
    if game.backend in _COMMAND_BACKENDS:
        check, _ = _COMMAND_BACKENDS[game.backend]
        check(game)
        return
    flow = load_flow(game_id)
    pages = flow.select(game.steps())
    target_for(game)
    resolution_for(game)
    check_templates(game.path("templates"), flow.required_features(pages))


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


def run_command(
    command: list[str], cwd: Path, timeout: int, *, stdout=None, cancelled: Callable[[], bool] | None = None
) -> int:
    kwargs = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.DEVNULL, stdout=stdout, **kwargs)
    try:
        if cancelled is None:
            return process.wait(timeout=timeout)
        deadline = time.monotonic() + timeout
        while True:
            if cancelled():
                raise RunAborted("任务已取消")
            remaining = deadline - time.monotonic()
            if remaining <= 1:
                return process.wait(timeout=max(remaining, 0))
            try:
                return process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                continue
    except BaseException:
        if process.poll() is not None:
            raise
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
            elif game.backend == "automas":
                run_automas(game_id, game)
            elif game.backend in _COMMAND_BACKENDS:
                _, run = _COMMAND_BACKENDS[game.backend]
                run(game, run_command)
            else:
                _run_native(game_id, game)
            print(f"[{game_id}] 完成", flush=True)
        except (subprocess.TimeoutExpired, TimeoutError):
            if game.backend != "native":
                raise RunAborted(f"[{game_id}] 超过 {game.timeout} 秒，队列已停止。请确认上游任务结束后再运行") from None
            print(f"[{game_id}] 超过 {game.timeout} 秒，已终止任务进程", file=sys.stderr, flush=True)
            all_succeeded = False
        except (ValueError, OSError) as exc:
            print(f"[{game_id}] {exc}", file=sys.stderr, flush=True)
            all_succeeded = False
    return all_succeeded
