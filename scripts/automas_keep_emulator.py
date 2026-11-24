from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from contextlib import suppress
from pathlib import Path

from core.automas_backend import (
    DEFAULT_PORT,
    _check_health,
    _check_success,
    _request,
    _snapshot_task_ids,
    _uuid,
    _validate_port,
)


_ADB_SERIAL = re.compile(r"(?:emulator-|127\.0\.0\.1:|localhost:)(\d{1,5})")
_TRACK_COMMAND = "track-devices"


def _adb_output(adb: Path, *args: str) -> bytes:
    return subprocess.run(
        [str(adb), *args],
        capture_output=True,
        check=True,
        timeout=15,
    ).stdout


def _select_serial(adb: Path, requested: str | None) -> str:
    devices = _adb_output(adb, "devices").decode(errors="replace")
    connected = []
    for line in devices.splitlines():
        fields = line.split()
        if len(fields) != 2 or fields[1] != "device":
            continue
        match = _ADB_SERIAL.fullmatch(fields[0])
        if match and 1 <= int(match[1]) <= 65535:
            connected.append(fields[0])

    if requested is not None:
        if requested in connected:
            return requested
        raise ValueError(f"ADB 未连接所选的本地模拟器 {requested}，请打开雷电实例并启用 ADB")
    if len(connected) == 1:
        return connected[0]
    if connected:
        raise ValueError(f"发现多个本地模拟器，请用 --serial 指定目标（{'、'.join(connected)}）")
    raise ValueError("ADB 未发现已连接的本地模拟器，请打开雷电实例并启用 ADB")


def _check_tracker(adb: Path) -> None:
    # 确认用户安装的 adb 支持作为 AUTO-MAS 的长驻监视进程。
    with subprocess.Popen(
        [str(adb), _TRACK_COMMAND],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ) as tracker:
        try:
            tracker.wait(timeout=1)
        except subprocess.TimeoutExpired:
            tracker.kill()
            return
    raise ValueError("此 adb.exe 的 track-devices 无法持续运行，请换用支持该命令的 adb.exe")


def _emulator_name(serial: str) -> str:
    return f"Daily Clear Hub 保留雷电（{serial}）"


def _register(port: int, adb: Path, serial: str) -> None:
    _validate_port(port)
    _check_health(port)
    response = _request(port, "/api/emulator/get", {})
    _check_success(response, "读取模拟器")
    data = response.get("data")
    if not isinstance(data, dict):
        raise ValueError("AUTO-MAS 返回的模拟器配置格式不兼容")

    name = _emulator_name(serial)
    matches = []
    for config in data.values():
        info = config.get("Info") if isinstance(config, dict) else None
        if isinstance(info, dict) and info.get("Name") == name:
            matches.append(info)
    if matches:
        if len(matches) == 1:
            info = matches[0]
            path = info.get("Path")
            if info.get("Type") == "general" and isinstance(path, str) and Path(path).resolve() == adb:
                return
        raise ValueError(f"已存在同名模拟器「{name}」，请在模拟器管理中先重命名该项")

    if _snapshot_task_ids(port):
        raise ValueError("请等 AUTO-MAS 的队列结束后再添加模拟器")
    response = _request(port, "/api/emulator/add", {})
    _check_success(response, "添加模拟器")
    emulator_id = _uuid(response.get("emulatorId"), "模拟器 ID")
    config = {"Type": "general", "Name": name, "Path": str(adb), "MaxWaitTime": 5}
    try:
        response = _request(port, "/api/emulator/update", {"emulatorId": emulator_id, "data": {"Info": config}})
        _check_success(response, "保存模拟器")
    except ValueError:
        # 只回收本次刚创建的条目，避免留下一个未配置的模拟器。
        with suppress(ValueError):
            response = _request(port, "/api/emulator/delete", {"emulatorId": emulator_id})
            _check_success(response, "撤销新建模拟器")
        raise


def _screenshot(adb: Path, serial: str) -> str:
    png = _adb_output(adb, "-s", serial, "exec-out", "screencap", "-p")
    if not png.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"ADB 未从 {serial} 返回有效的 PNG 截图")
    with tempfile.NamedTemporaryFile(prefix="daily-clear-hub-adb-", suffix=".png", delete=False) as image:
        image.write(png)
        return image.name


def main() -> int:
    parser = argparse.ArgumentParser(description="在 AUTO-MAS 中连接已打开的雷电实例")
    parser.add_argument("action", choices=("register", "screenshot"))
    parser.add_argument("--adb", type=Path, required=True, help="雷电安装目录中的 adb.exe")
    parser.add_argument("--serial", help="存在多个实例时指定 adb devices 显示的设备编号")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="本机 AUTO-MAS 端口")
    args = parser.parse_args()

    try:
        adb = args.adb.resolve()
        if not adb.is_file() or adb.name.casefold() != "adb.exe":
            raise ValueError("请用 --adb 指定雷电安装目录中的 adb.exe")
        serial = _select_serial(adb, args.serial)
        if args.action == "screenshot":
            print(_screenshot(adb, serial))
        else:
            _check_tracker(adb)
            _register(args.port, adb, serial)
            print(f"模拟器  {_emulator_name(serial)}")
            print(f"模拟器实例  {_TRACK_COMMAND} | {serial}")
    except subprocess.CalledProcessError as exc:
        parser.exit(1, f"执行 ADB 失败，退出码 {exc.returncode}。\n")
    except subprocess.TimeoutExpired:
        parser.exit(1, "等待 ADB 响应超时。\n")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
