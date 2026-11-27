"""Run a finite NKAS job and write the result watched by AUTO-MAS."""

from __future__ import annotations

import argparse
import http.client
import json
import os
import socket
import subprocess
import sys
import time
import webbrowser
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent
STATUS = "DCH_NKAS_STATUS "
STATUS_PATH_ENV = "DAILY_CLEAR_HUB_NKAS_STATUS_PATH"
DONE = "DCH_NKAS_DONE"
FAILED = "DCH_NKAS_FAILED"
SUCCESS_STATES = {"complete", "already_complete"}


@contextmanager
def run_lock():
    import msvcrt

    with (ROOT / ".run.lock").open("a+b") as handle:
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise ValueError("另一个 AUTO-MAS NIKKE 任务仍在执行") from exc
        yield


def boost(settings: dict, log) -> None:
    route = settings.get("uu")
    if not isinstance(route, dict) or not isinstance(game := route.get("game"), str) or not game.strip():
        raise ValueError("启用了 UU，请在 nikke.json 中填写 uu.game（UU 游戏卡片全名）")
    root = ROOT.parent / "uu-automas"
    python = root / ".venv" / "Scripts" / "python.exe"
    helper = root / "uu_boost.py"
    if not python.is_file() or not helper.is_file():
        raise ValueError("找不到 UU 运行环境，请重新执行安装脚本并加上 -WithUu")
    command = [str(python), "-X", "utf8", "-u", str(helper), f"--game={game.strip()}"]
    for key in ("region", "exe"):
        if isinstance(value := route.get(key), str) and value.strip():
            command.append(f"--{key}={value.strip()}")
    log("切换网易 UU 加速")
    result = subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace", timeout=120)
    for line in (result.stdout + "\n" + result.stderr).splitlines():
        if line.strip():
            log(line)
    if result.returncode:
        raise ValueError("UU 未确认游戏已加速")


def run_nkas(upstream: Path, profile: str, log, diagnostic_log: Path) -> None:
    python = upstream / "toolkit" / "python.exe"
    if not python.is_file() or not (upstream / "main.py").is_file():
        raise ValueError("没有找到 NKAS 完整包，请重新执行 setup-windows.ps1 -Games nikke")
    command = [str(python), "-X", "utf8", "-u", str(ROOT / "run_once.py"), profile]
    terminal = []
    failure_detail = ""
    # The upstream launcher can leave detached processes running. Use a
    # status file and a regular output file so inherited handles cannot block completion.
    with TemporaryDirectory(prefix="daily-clear-nkas-") as directory, diagnostic_log.open("wb") as output:
        report = Path(directory) / "status.log"
        report.touch()
        env = {**os.environ, STATUS_PATH_ENV: str(report)}
        with subprocess.Popen(
            command, cwd=upstream, env=env, stdin=subprocess.DEVNULL,
            stdout=output, stderr=subprocess.STDOUT,
        ) as process, report.open(encoding="utf-8", errors="replace") as stream:
            while True:
                try:
                    code = process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    code = None
                while True:
                    offset = stream.tell()
                    line = stream.readline()
                    if not line.endswith("\n"):
                        stream.seek(offset)
                        break
                    if line.startswith(STATUS):
                        message = line[len(STATUS):].strip()
                        state, _, detail = message.partition(" ")
                        if state == "log":
                            log(f"NKAS {detail}")
                            continue
                        if state in SUCCESS_STATES or state in {"failed", "stopped"}:
                            terminal.append(state)
                        if state == "failed" and detail:
                            failure_detail = detail
                        log(f"NKAS {message}")
                if code is not None:
                    break
    if code == 0 and len(terminal) == 1 and terminal[0] in SUCCESS_STATES:
        return
    reason = failure_detail or f"NKAS 未确认本轮完成（退出码 {code}）"
    raise ValueError(f"{reason}。子进程日志 {diagnostic_log.name}")


def load_settings() -> tuple[dict, Path, str]:
    settings = json.loads((ROOT / "nikke.json").read_text(encoding="utf-8-sig"))
    local = json.loads((ROOT / "local.json").read_text(encoding="utf-8-sig"))
    upstream = Path(local["nkas_root"])
    profile = settings.get("profile", "nkas")
    if not isinstance(profile, str) or not profile.strip() or any(
        character in profile for character in '<>:"/\\|?*'
    ) or profile in (".", "..", "template"):
        raise ValueError("nikke.json 的 profile 应为 NKAS 中已保存的实例名")
    return settings, upstream, profile


def wait_for_config_ui(process: subprocess.Popen, port: int) -> None:
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline and process.poll() is None:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
        try:
            connection.request("GET", "/app/")
            if connection.getresponse().status in (200, 302, 307, 401, 403):
                return
        except (OSError, http.client.HTTPException):
            pass
        finally:
            connection.close()
        time.sleep(0.5)
    raise ValueError("NKAS 配置页启动失败，请查看配置会话日志")


def configure() -> int:
    _, upstream, profile = load_settings()
    python = upstream / "toolkit" / "python.exe"
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    command = [
        str(python), "-X", "utf8", "-u", str(ROOT / "config_ui.py"),
        "--host", "127.0.0.1", "--port", str(port),
    ]
    with run_lock(), (ROOT / "logs" / "configure.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, cwd=upstream, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        try:
            wait_for_config_ui(process, port)
            url = f"http://127.0.0.1:{port}/app/"
            if (upstream / "config" / f"{profile}.json").is_file():
                url += f"#/i/{quote(profile, safe='')}/schedule"
            print(f"NKAS 配置页：{url}", flush=True)
            print(f"NKAS 配置页：{url}", file=log, flush=True)
            webbrowser.open(url)
            return process.wait()
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uu", action="store_true")
    parser.add_argument("--configure", action="store_true")
    args = parser.parse_args()
    if args.configure:
        try:
            if os.name != "nt":
                raise ValueError("NKAS 托管需要 Windows")
            return configure()
        except (AttributeError, KeyError, OSError, TypeError, ValueError) as exc:
            print(exc, file=sys.stderr, flush=True)
            return 1
    started = datetime.now()
    run_id = f"{started:%Y%m%d-%H%M%S-%f}"
    path = ROOT / "logs" / f"run-{run_id}.log"
    with path.open("x", encoding="utf-8", buffering=1) as stream:
        def log(message: str) -> None:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S.%f} {message}", file=stream, flush=True)

        log("准备 NIKKE 国际服日常")
        try:
            if os.name != "nt":
                raise ValueError("NKAS 托管需要 Windows")
            with run_lock():
                settings, upstream, profile = load_settings()
                if not (upstream / "config" / f"{profile}.json").is_file():
                    raise ValueError("找不到该 NKAS 实例的配置，请先在 NKAS 保存一次")
                if args.uu:
                    boost(settings, log)
                run_nkas(upstream, profile, log, path.with_name(f"child-{run_id}.log"))
        except (AttributeError, KeyError, OSError, TypeError, ValueError, subprocess.SubprocessError) as exc:
            log(f"{FAILED} {exc}")
            return 1
        log(DONE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
