from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import NamedTemporaryFile


POPUP_ENTRY = "清理弹窗_入口"
HOME_MARKER = "检测主界面_标志"
NOTICE = "Hub_清弹窗_关闭公告"
WISH = "Hub_清弹窗_关闭祈愿宣传"
SIGN_IN = "Hub_清弹窗_领取每日签到"
KNOWN_POPUPS = [NOTICE, WISH, SIGN_IN]


def popup_click(recognition: str, params: dict, target_offset: list[int], message: str) -> dict:
    return {
        "recognition": {"type": recognition, "param": params},
        "action": {"type": "Click", "param": {"target_offset": target_offset}},
        "max_hit": 3,
        "post_delay": 1000,
        "next": ["清弹窗"],
        "focus": {"Node.PipelineNode.Succeeded": message},
    }


POPUP_OVERRIDES = {
    NOTICE: popup_click(
        "TemplateMatch",
        {"template": ["popup_x/关闭.png"], "roi": [1110, 35, 115, 85], "threshold": 0.88},
        [18, 18, -36, -36],
        "已关闭崩坏学园 2 公告",
    ),
    WISH: popup_click(
        "TemplateMatch",
        {"template": ["popup_x/关闭2.png"], "roi": [990, 153, 95, 84], "threshold": 0.86},
        [18, 16, -36, -32],
        "已关闭崩坏学园 2 祈愿宣传",
    ),
    SIGN_IN: popup_click(
        "And",
        {
            "all_of": [
                {"recognition": "OCR", "roi": [548, 199, 183, 62], "expected": ["^每日签到$"]},
                {
                    "recognition": "TemplateMatch",
                    "template": ["btn_lingqu.png"],
                    "roi": [830, 447, 235, 104],
                    "threshold": 0.88,
                },
            ],
            "box_index": 1,
        },
        [76, 20, -152, -40],
        "已点击每日签到领取",
    ),
    "清弹窗": {
        "next": [*KNOWN_POPUPS, "关掉x", "领取", "清弹窗_点领取奖励", "生日弹窗", HOME_MARKER],
        "on_error": [HOME_MARKER, "首页"],
    },
    # A popup may appear while the game is returning from a different page.
    "检测主界面": {"next": [*KNOWN_POPUPS, HOME_MARKER]},
    "检测主界面_终": {"next": [*KNOWN_POPUPS, HOME_MARKER], "on_error": [HOME_MARKER, "拉回主界面"]},
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
    for name, fields in POPUP_OVERRIDES.items():
        node = overrides.setdefault(name, {})
        if not isinstance(node, dict):
            raise ValueError(f"{name} 的清理弹窗覆盖配置应为对象")
        for field, value in fields.items():
            if field in node:
                if node[field] != value:
                    raise ValueError(f"{name} 已有不同的清理弹窗 {field} 配置，请核对后再应用修复")
            else:
                node[field] = value
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
    parser = argparse.ArgumentParser(description="为 MaaBH2 清理弹窗任务添加公告、祈愿宣传和每日签到识别")
    parser.add_argument("interface", type=Path, help="MaaBH2 来源目录的 interface.json")
    args = parser.parse_args()
    try:
        applied = patch_popup_task(args.interface)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")
    print("已应用 MaaBH2 清理弹窗修复" if applied else "MaaBH2 清理弹窗修复已存在")


if __name__ == "__main__":
    main()
