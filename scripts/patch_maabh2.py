from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import NamedTemporaryFile


POPUP_ENTRY = "清理弹窗_入口"
LOGIN_ENTRY = "国服进入游戏_开始"
LOGIN_HANDOFF = "Hub_进入游戏_交接清弹窗"
LOGIN_PROMPT = "Hub_进入游戏_点击继续"
LOGIN_ACCOUNT = "进入游戏_识别切换账号"
LOGIN_UPDATE = "国服进入游戏_检测更新"
LOGIN_UPDATE_WAIT = "国服进入游戏_等更新完成"
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


LOGIN_READY = [LOGIN_HANDOFF, LOGIN_PROMPT, LOGIN_ACCOUNT]
PREVIOUS_LOGIN_NEXT = {
    LOGIN_ENTRY: [LOGIN_HANDOFF, LOGIN_UPDATE, LOGIN_ACCOUNT],
    LOGIN_UPDATE_WAIT: [LOGIN_HANDOFF, LOGIN_ACCOUNT],
    LOGIN_ACCOUNT: [LOGIN_HANDOFF],
}

LOGIN_OVERRIDES = {
    LOGIN_HANDOFF: {
        "recognition": {
            "type": "Or",
            "param": {
                "any_of": [
                    HOME_MARKER,
                    *({"recognition": POPUP_OVERRIDES[node]["recognition"]} for node in KNOWN_POPUPS),
                ],
            },
        },
        "action": {"type": "DoNothing"},
        "focus": {"Node.PipelineNode.Succeeded": "已进入游戏，后续由「3. 清理弹窗」处理"},
    },
    LOGIN_ENTRY: {
        "timeout": 60000,
        "next": [LOGIN_HANDOFF, LOGIN_UPDATE, LOGIN_PROMPT, LOGIN_ACCOUNT],
        "focus": {"Node.PipelineNode.Failed": "60 秒内未识别到登录入口或游戏内界面，请检查模拟器画面"},
    },
    LOGIN_UPDATE_WAIT: {
        "timeout": 300000,
        "next": LOGIN_READY,
        "focus": {"Node.PipelineNode.Failed": "等待更新结束超过 5 分钟，请检查游戏内下载进度"},
    },
    LOGIN_PROMPT: {
        "recognition": {
            "type": "OCR",
            "param": {
                "roi": [350, 550, 580, 170],
                "expected": [
                    r"屏\s*幕\s*继\s*续",
                    r"^(?:抚摸|点击|轻触)\s*(?:屏幕\s*)?进入游戏[！!。]?$",
                ],
            },
        },
        "action": {"type": "Click", "param": {"target": [640, 668]}},
        "max_hit": 4,
        "post_delay": 2000,
        "timeout": 60000,
        "next": LOGIN_READY,
        "focus": {
            "Node.PipelineNode.Succeeded": "已识别标题页继续提示，点击进入游戏",
            "Node.PipelineNode.Failed": "点击继续后未识别到游戏内界面，请检查登录或加载状态",
        },
    },
    LOGIN_ACCOUNT: {
        # Recheck the title screen between taps so the next tap cannot land on an in-game popup.
        "repeat": 1,
        "pre_delay": 0,
        "max_hit": 4,
        "timeout": 60000,
        "next": LOGIN_READY,
        "focus": {"Node.PipelineNode.Failed": "点击登录后 60 秒内未识别到游戏内界面，请检查是否有登录或授权提示"},
    },
}


def merge_overrides(task: dict, fields_by_node: dict, previous_next: dict) -> bool:
    if task.get("pipeline_override") is None:
        task["pipeline_override"] = {}
    overrides = task["pipeline_override"]
    if not isinstance(overrides, dict):
        raise ValueError(f"{task['entry']} 的 pipeline_override 应为对象")
    changed = False
    for name, fields in fields_by_node.items():
        node = overrides.setdefault(name, {})
        if not isinstance(node, dict):
            raise ValueError(f"{name} 的流水线覆盖配置应为对象")
        for field, value in fields.items():
            if field in node:
                if node[field] == value:
                    continue
                if field != "next" or name not in previous_next or node[field] != previous_next[name]:
                    raise ValueError(f"{name} 已有不同的 {field} 配置，请核对后再应用修复")
            node[field] = value
            changed = True
    return changed


def patch_project(interface: Path) -> bool:
    project = json.loads(interface.read_text(encoding="utf-8-sig"))
    if not isinstance(project, dict) or (
        project.get("name"), project.get("version")
    ) != ("MaaBh2", "0.3.6"):
        raise ValueError("MaaBH2 修复需要 0.3.6 的 interface.json")

    tasks = project.get("task")
    if not isinstance(tasks, list):
        raise ValueError("MaaBH2 项目缺少任务列表")
    changed = False
    for entry, overrides, previous_next in (
        (POPUP_ENTRY, POPUP_OVERRIDES, {}),
        (LOGIN_ENTRY, LOGIN_OVERRIDES, PREVIOUS_LOGIN_NEXT),
    ):
        matches = [task for task in tasks if isinstance(task, dict) and task.get("entry") == entry]
        if len(matches) != 1:
            raise ValueError(f"MaaBH2 项目中应有且只有一个 {entry} 任务")
        if merge_overrides(matches[0], overrides, previous_next):
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
    parser = argparse.ArgumentParser(description="修复 MaaBH2 登录交接及公告、祈愿宣传和每日签到处理")
    parser.add_argument("interface", type=Path, help="MaaBH2 来源目录的 interface.json")
    args = parser.parse_args()
    try:
        applied = patch_project(args.interface)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")
    print("已应用 MaaBH2 登录与弹窗修复" if applied else "MaaBH2 登录与弹窗修复已存在")


if __name__ == "__main__":
    main()
