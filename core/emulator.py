from __future__ import annotations

import platform
import subprocess
from pathlib import Path
from typing import Any


class EmulatorError(RuntimeError):
    pass


class LDPlayerEmulator:
    """雷电模拟器控制封装，仅在 Windows 上可用。"""

    def __init__(self, ldplayer_root: str | Path, adb_path: str | Path | None = None):
        self.ldplayer_root = Path(ldplayer_root)
        self.adb_path = Path(adb_path) if adb_path else self.ldplayer_root / "adb.exe"
        self.ldconsole_path = self.ldplayer_root / "ldconsole.exe"

    @staticmethod
    def is_supported() -> bool:
        return platform.system() == "Windows"

    def _ensure_supported(self) -> None:
        if not self.is_supported():
            raise EmulatorError("LDPlayer 控制仅支持 Windows 环境")

    def _run_ldconsole(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        self._ensure_supported()
        if not self.ldconsole_path.exists():
            raise EmulatorError(f"未找到 ldconsole: {self.ldconsole_path}")
        return subprocess.run(
            [str(self.ldconsole_path), *args],
            capture_output=True,
            text=True,
            check=check,
        )

    def launch(self, index: int = 0) -> None:
        self._run_ldconsole("launch", "--index", str(index))

    def quit(self, index: int = 0) -> None:
        self._run_ldconsole("quit", "--index", str(index))

    def run_app(self, package: str, index: int = 0) -> None:
        self._run_ldconsole("runapp", "--index", str(index), "--packagename", package)

    def kill_app(self, package: str, index: int = 0) -> None:
        self._run_ldconsole("killapp", "--index", str(index), "--packagename", package)

    def adb_shell(self, command: str, index: int = 0) -> subprocess.CompletedProcess[str]:
        self._ensure_supported()
        if not self.adb_path.exists():
            raise EmulatorError(f"未找到 adb: {self.adb_path}")
        return subprocess.run(
            [
                str(self.ldconsole_path),
                "adb",
                "--index",
                str(index),
                "--command",
                command,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

    def set_resolution(self, width: int, height: int, dpi: int, index: int = 0) -> None:
        self._run_ldconsole(
            "modify",
            "--index",
            str(index),
            "--resolution",
            f"{width},{height},{dpi}",
        )

    @classmethod
    def from_config(cls, emulator_config: dict[str, Any]) -> "LDPlayerEmulator":
        root = emulator_config.get("ldplayer_root", "")
        if not root:
            raise EmulatorError("config.local.yaml 未配置 emulator.ldplayer_root")
        return cls(
            ldplayer_root=root,
            adb_path=emulator_config.get("adb"),
        )
