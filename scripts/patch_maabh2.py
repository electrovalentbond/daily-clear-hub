from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import NamedTemporaryFile


POPUP_ENTRY = "清理弹窗_入口"
HOME_MARKER = "检测主界面_标志"
HOME_RECHECKS = {
    "清弹窗": [HOME_MARKER, "首页"],
    "检测主界面_终": [HOME_MARKER, "拉回主界面"],
}


def patch_popup_task(interface: Path) -> bool:
    project = json.loads(interface.read_text(encoding="utf-8-sig"))
    if not isinstance(project, dict) or (
        project.get("name"), project.get("version")
    ) != ("MaaBh2", "0.3.6"):
        raise ValueError("清理弹窗修复需要 MaaBH2 0.3.6 的 interface.json")

    tasks = project.get("task")
    if not isinstance(tasks, list):
        raise ValueError("MaaBH2 项目缺少任务列表")
    matches = [task for task in tasks if isinstance(task, dict) and task.get("entry") == POPUP_ENTRY]
    if len(matches) != 1:
        raise ValueError("MaaBH2 项目中应有且只有一个清理弹窗任务")

    task = matches[0]
    if task.get("pipeline_override") is None:
        task["pipeline_override"] = {}
    overrides = task["pipeline_override"]
    if not isinstance(overrides, dict):
        raise ValueError("清理弹窗任务的 pipeline_override 应为对象")
    changed = False
    for name, candidates in HOME_RECHECKS.items():
        node = overrides.setdefault(name, {})
        if not isinstance(node, dict):
            raise ValueError(f"{name} 的清理弹窗覆盖配置应为对象")
        if "on_error" in node:
            if node["on_error"] != candidates:
                raise ValueError(f"{name} 已有不同的清理弹窗回退配置，请核对后再应用修复")
            continue
        # Keep checking for a late home screen even after the click limit is reached.
        node["on_error"] = candidates
        changed = True
    if not changed:
        return False

    content = json.dumps(project, ensure_ascii=False, indent=2) + "\n"
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=interface.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(content)
            stream.close()
            temporary.replace(interface)
        finally:
            temporary.unlink(missing_ok=True)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="修复 MaaBH2 清理弹窗任务的首页复检")
    parser.add_argument("interface", type=Path, help="MaaBH2 来源目录的 interface.json")
    args = parser.parse_args()
    try:
        applied = patch_popup_task(args.interface)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")
    print("已应用 MaaBH2 清理弹窗修复" if applied else "MaaBH2 清理弹窗修复已存在")


if __name__ == "__main__":
    main()
