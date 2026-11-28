"""Use the bound Win32 game window in MaaGakumasu's DMM shutdown task."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath


DMM_RESOURCES = {"DMM", "DMM插件汉化版"}
DMM_PATH = "resource/DMM"
ANDROID_ACTION = {"type": "StopApp", "param": {"package": "com.bandainamcoent.idolmaster_gakuen"}}
DMM_SHUTDOWN = {"Shutdown": {"action": {"type": "StopApp", "param": {"package": ""}}}}


def patch(interface: Path) -> bool:
    project = json.loads(interface.read_text(encoding="utf-8-sig"))
    dmm_path = PureWindowsPath(DMM_PATH)
    dmm = [
        resource for resource in project.get("resource", [])
        if any(PureWindowsPath(path) == dmm_path for path in resource.get("path", []))
    ]
    if {resource.get("name") for resource in dmm} != DMM_RESOURCES or not all(
        resource.get("controller") == ["PC"] for resource in dmm
    ):
        raise ValueError("MaaGakumasu DMM resource layout has changed")

    base = interface.parent / "resource/base/pipeline/Shutdown.json"
    node = json.loads(base.read_text(encoding="utf-8-sig")).get("Shutdown", {})
    if node.get("action") != ANDROID_ACTION or node.get("recognition", {}).get("type") != "DirectHit":
        raise ValueError("MaaGakumasu base Shutdown node has changed")

    overlay = interface.parent / DMM_PATH / "pipeline/Shutdown.json"
    if overlay.exists():
        if json.loads(overlay.read_text(encoding="utf-8-sig")) == DMM_SHUTDOWN:
            return False
        raise ValueError("MaaGakumasu already has a different DMM Shutdown node")

    # An explicit empty package makes Win32 StopApp use the bound HWND's PID.
    # Omitting the field would inherit the Android package from the base resource.
    temporary = overlay.with_suffix(".tmp")
    temporary.write_text(json.dumps(DMM_SHUTDOWN, indent=2) + "\n", encoding="utf-8")
    temporary.replace(overlay)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("interface", type=Path)
    args = parser.parse_args()
    patch(args.interface)


if __name__ == "__main__":
    main()
