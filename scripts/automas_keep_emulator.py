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


_ADB_SERIAL = re.compile(r"(emulator-|127\.0\.0\.1:|localhost:)([0-9]{1,5})")
_TRACK_COMMAND = "track-devices"


def _program_output(program: Path, *args: str) -> bytes:
    return subprocess.run(
        [str(program), *args],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
        timeout=15,
    ).stdout


def _ldplayer_addresses(adb: Path, indexes: list[int]) -> list[str]:
    ports = {str(index): 5555 + 2 * index for index in indexes}
    if any(not 5555 <= port <= 65535 for port in ports.values()):
        raise ValueError("雷电实例编号超出默认 ADB 端口范围")
    consoles = [adb.with_name(name) for name in ("ldconsole.exe", "dnconsole.exe")]
    console = next((path for path in consoles if path.is_file()), None)
    if console is None:
        raise ValueError("找不到雷电控制台，请用 --adb 指定雷电安装目录里的 adb.exe")
    try:
        instances = _program_output(console, "list2").decode(errors="replace")
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"无法用 {console.name} list2 读取雷电实例（退出码 {exc.returncode}）") from exc
    states = {}
    for line in instances.splitlines():
        index, _, info = line.partition(",")
        fields = info.rsplit(",", 8)
        if len(fields) == 9:
            # list2: index, title, hwnd, bind hwnd, in_android, pid, VBox pid, width, height, DPI.
            states[index.strip()] = fields[3].strip()
    for index in ports:
        if index not in states:
            raise ValueError(f"找不到雷电实例 {index}，请用 {console.name} list2 核对实际编号")
        if states[index] != "1":
            raise ValueError(f"请先打开雷电实例 {index} 并等待进入 Android 桌面")
    return [f"127.0.0.1:{port}" for port in ports.values()]


def _local_devices(adb: Path) -> dict[str, str]:
    devices = {}
    for line in _program_output(adb, "devices").decode(errors="replace").splitlines():
        fields = line.split()
        if len(fields) != 2:
            continue
        match = _ADB_SERIAL.fullmatch(fields[0])
        if match and 1 <= int(match[2]) <= 65535:
            devices[fields[0]] = fields[1]
    return devices


def _connect_loopback(adb: Path, serial: str) -> str:
    try:
        output = _program_output(adb, "connect", serial)
    except subprocess.CalledProcessError as exc:
        output = exc.stderr or exc.output or b""
    except subprocess.TimeoutExpired:
        return "连接超时"
    return output.decode(errors="replace").strip()


def _verify_loopback(adb: Path, address: str) -> None:
    try:
        state = _program_output(adb, "-s", address, "get-state").decode(errors="replace").strip()
    except subprocess.CalledProcessError as exc:
        state = (exc.stderr or exc.output or b"").decode(errors="replace").strip() or f"退出码 {exc.returncode}"
    if state != "device":
        raise ValueError(f"ADB 地址 {address} 未就绪（{state or '未返回状态'}），请确认实例已打开并启用 ADB 本地连接")


def _select_serials(adb: Path, requested: list[str]) -> list[str]:
    devices = _local_devices(adb)
    if not requested:
        connected = [serial for serial, state in devices.items() if state == "device"]
        if len(connected) == 1:
            return connected
        if connected:
            raise ValueError(f"发现多个本地模拟器，请用 --serial 指定目标，可重复传入（{'、'.join(connected)}）")
        states = "、".join(f"{serial}={state}" for serial, state in devices.items()) or "无"
        raise ValueError(f"ADB 未发现可用的本地模拟器（{states}），请打开雷电实例并启用 ADB 本地连接")

    serials = list(dict.fromkeys(requested))
    for serial in serials:
        match = _ADB_SERIAL.fullmatch(serial)
        if not match or not 1 <= int(match[2]) <= 65535:
            raise ValueError(f"无效的本地模拟器地址 {serial}，请使用 adb devices 显示的序列号或已确认的本地端口")
        is_loopback = match[1] != "emulator-"
        detail = ""
        if is_loopback and devices.get(serial) in (None, "offline"):
            # 显式指定端口才主动连接。AUTO-MAS 在运行时也会重连这个地址。
            detail = _connect_loopback(adb, serial)
            devices = _local_devices(adb)
        if devices.get(serial) != "device":
            state = devices.get(serial, "未出现在 adb devices 中")
            hint = "请确认目标实例已进入 Android 桌面并启用 ADB 本地连接"
            extra = f"。ADB 连接结果：{detail}" if detail else ""
            raise ValueError(f"ADB 未连接所选的本地模拟器 {serial}（{state}），{hint}{extra}")
        if is_loopback:
            _verify_loopback(adb, serial)
    return serials


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
    png = _program_output(adb, "-s", serial, "exec-out", "screencap", "-p")
    if not png.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"ADB 未从 {serial} 返回有效的 PNG 截图")
    with tempfile.NamedTemporaryFile(prefix="daily-clear-hub-adb-", suffix=".png", delete=False) as image:
        image.write(png)
        return image.name


def main() -> int:
    parser = argparse.ArgumentParser(description="在 AUTO-MAS 中连接已打开的雷电实例")
    parser.add_argument("action", choices=("register", "screenshot"))
    parser.add_argument("--adb", type=Path, required=True, help="雷电安装目录中的 adb.exe")
    target = parser.add_mutually_exclusive_group()
    target.add_argument(
        "--ld-index", action="append", default=[], type=int,
        help="用雷电实例编号连接默认本机 ADB 端口；register 可重复指定",
    )
    target.add_argument(
        "--serial", action="append", default=[],
        help="指定 adb devices 显示的序列号或已确认的本地端口；register 可重复指定",
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="本机 AUTO-MAS 端口")
    args = parser.parse_args()

    try:
        adb = args.adb.resolve()
        if not adb.is_file() or adb.name.casefold() != "adb.exe":
            raise ValueError("请用 --adb 指定雷电安装目录中的 adb.exe")
        if args.action == "screenshot" and max(len(args.serial), len(args.ld_index)) > 1:
            raise ValueError("screenshot 只接受一个 --serial 或 --ld-index")
        requested = _ldplayer_addresses(adb, args.ld_index) if args.ld_index else args.serial
        serials = _select_serials(adb, requested)
        if args.action == "screenshot":
            print(_screenshot(adb, serials[0]))
        else:
            _check_tracker(adb)
            for serial in serials:
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
