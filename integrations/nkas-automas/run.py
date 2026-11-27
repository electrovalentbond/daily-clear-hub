"""Run a finite NKAS job and write the result watched by AUTO-MAS."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory


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


def run_nkas(upstream: Path, profile: str, log) -> bool:
    python = upstream / "toolkit" / "python.exe"
    if not python.is_file() or not (upstream / "main.py").is_file():
        raise ValueError("没有找到 NKAS 完整包，请重新执行 setup-windows.ps1 -Games nikke")
    command = [str(python), "-X", "utf8", "-u", str(ROOT / "run_once.py"), profile]
    terminal = []
    # The upstream launcher can leave detached processes running. Use a
    # separate status file so inherited console handles cannot block completion.
    with TemporaryDirectory(prefix="daily-clear-nkas-") as directory:
        report = Path(directory) / "status.log"
        report.touch()
        env = {**os.environ, STATUS_PATH_ENV: str(report)}
        with subprocess.Popen(
            command, cwd=upstream, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ) as process, report.open(encoding="utf-8") as stream:
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
                        state = message.split(" ", 1)[0]
                        if state in SUCCESS_STATES or state in {"failed", "stopped"}:
                            terminal.append(state)
                        log(f"NKAS {message}")
                if code is not None:
                    return code == 0 and terminal in (["complete"], ["already_complete"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uu", action="store_true")
    args = parser.parse_args()
    started = datetime.now()
    path = ROOT / "logs" / f"run-{started:%Y%m%d-%H%M%S-%f}.log"
    with path.open("x", encoding="utf-8", buffering=1) as stream:
        def log(message: str) -> None:
            print(f"{datetime.now():%Y-%m-%d %H:%M:%S.%f} {message}", file=stream, flush=True)

        log("准备 NIKKE 国际服日常")
        try:
            if os.name != "nt":
                raise ValueError("NKAS 托管需要 Windows")
            with run_lock():
                settings = json.loads((ROOT / "nikke.json").read_text(encoding="utf-8-sig"))
                local = json.loads((ROOT / "local.json").read_text(encoding="utf-8-sig"))
                upstream = Path(local["nkas_root"])
                profile = settings.get("profile", "nkas")
                if not isinstance(profile, str) or not profile.strip() or any(
                    character in profile for character in '<>:"/\\|?*'
                ) or profile in (".", "..", "template"):
                    raise ValueError("nikke.json 的 profile 应为 NKAS 中已保存的实例名")
                if not (upstream / "config" / f"{profile}.json").is_file():
                    raise ValueError("找不到该 NKAS 实例的配置，请先在 NKAS 保存一次")
                if args.uu:
                    boost(settings, log)
                if not run_nkas(upstream, profile, log):
                    raise ValueError("NKAS 未确认本轮完成，请查看 NKAS 自己的 log 目录")
        except (AttributeError, KeyError, OSError, TypeError, ValueError, subprocess.SubprocessError) as exc:
            log(f"{FAILED} {exc}")
            return 1
        log(DONE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
