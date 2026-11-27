"""Select and verify a game profile in the Windows UU desktop client."""

from __future__ import annotations

import argparse
import ctypes
import os
import re
import subprocess
import sys
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path


_CLIENTS = {"uu.exe", "uu_launcher.exe"}
_SEARCH_LABELS = {"搜索", "搜索游戏", "搜索游戏/应用", "请输入游戏名称", "搜索游戏名称"}
_START = {"开始加速", "立即加速", "一键加速"}
_REGION_LABELS = {"游戏服", "区服", "游戏区服", "加速区服", "选择区服"}
_STOP_NOTICES = (
    "重新加速将断开正在加速游戏连接",
    "停止加速将断开当前游戏连接",
    "停止加速后当前游戏将断开连接",
    "其他游戏正在加速",
)
_DISALLOWED_CONFIRMATION = ("付费", "购买", "充值", "开通", "支付", "订阅", "扣费")


class BoostError(RuntimeError):
    pass


def normalize(text: str) -> str:
    return "".join(unicodedata.normalize("NFKC", text).casefold().split())


@dataclass(frozen=True)
class Label:
    text: str
    rect: tuple[int, int, int, int]
    role: str = ""

    @property
    def x(self) -> int:
        return (self.rect[0] + self.rect[2]) // 2

    @property
    def y(self) -> int:
        return (self.rect[1] + self.rect[3]) // 2

    @property
    def height(self) -> int:
        return self.rect[3] - self.rect[1]


@dataclass(frozen=True)
class Page:
    width: int
    height: int
    labels: tuple[Label, ...]

    def exact(self, names: set[str]) -> list[Label]:
        wanted = {normalize(name) for name in names}
        matches = []
        for label in self.labels:
            if normalize(label.text) not in wanted or label.role == "Edit":
                continue
            if any(
                abs(label.x - seen.x) <= max(label.height, seen.height)
                and abs(label.y - seen.y) <= min(label.height, seen.height)
                for seen in matches
            ):
                continue
            matches.append(label)
        return matches

    def search(self, previous_query: str) -> Label | None:
        edits = [
            label for label in self.labels
            if label.role == "Edit" and label.y < self.height / 4
        ]
        if len(edits) == 1:
            return edits[0]
        names = _SEARCH_LABELS | ({previous_query} if previous_query else set())
        options = [
            label for label in self.exact(names)
            if label.y < self.height / 4
        ]
        if len(options) == 1:
            return options[0]
        # Some versions keep the old query in a custom-drawn field with no
        # accessible edit. The search field is on the dynamic wallpaper row.
        navigation = self.exact({"动态壁纸"})
        if len(navigation) == 1:
            tab = navigation[0]
            trailing = [
                label for label in self.labels
                if not label.role and label.rect[0] > tab.rect[2]
                and abs(label.y - tab.y) <= max(label.height, tab.height)
            ]
            if len(trailing) == 1:
                return trailing[0]
        return None

    def search_result(self, search: Label, game: str) -> Label | None:
        # Search suggestions are anchored to the search box. The search text
        # itself and a same-name tile elsewhere in the library are separate.
        options = [
            label for label in self.exact({game})
            if search.rect[3] <= label.y < search.y + self.height / 2
            and abs(label.x - search.x) < self.width / 4
        ]
        return options[0] if len(options) == 1 else None

    def titled_action(self, game: str, words: set[str]) -> Label | None:
        pairs = [
            button for button in self.exact(words)
            if any(
                title.y < button.y < title.y + self.height / 5
                and abs(button.x - title.x) < self.width / 5
                for title in self.exact({game})
            )
        ]
        return pairs[0] if len(pairs) == 1 else None

    def active_button(self) -> Label | None:
        buttons = self.exact({"停止加速"})
        indicators = self.exact({"启动游戏", "游戏延迟", "丢包率", "网络监控"})
        return buttons[0] if len(buttons) == 1 and indicators else None

    def has_confirmation(self) -> bool:
        payment = self.exact({"立即支付", "立即购买", "立即开通", "确认支付", "开通会员"})
        return bool(payment or self.exact({"取消"}) and self.exact({"确定", "确认", "继续加速"}))

    def region_field(self, region: str) -> tuple[Label | None, bool]:
        fields = []
        for label in self.labels:
            text = normalize(label.text)
            if ":" in text and text.split(":", 1)[0] in _REGION_LABELS:
                fields.append((label, text.split(":", 1)[1] == normalize(region)))
        if len(fields) == 1:
            return fields[0]
        captions = self.exact(_REGION_LABELS)
        if len(captions) != 1:
            return None, False
        caption = captions[0]
        selected = any(
            caption.x < label.x < caption.x + self.width / 4
            and abs(label.y - caption.y) <= max(label.height, caption.height)
            for label in self.exact({region})
        )
        return caption, selected

    def region_option(self, region: str) -> Label | None:
        captions = self.exact({"选择区服", "选择游戏区服", "区服选择"})
        matching = [
            option for option in self.exact({region})
            if any(caption.rect[3] <= option.y < caption.y + self.height * 0.75
                   and abs(option.x - caption.x) < self.width / 3 for caption in captions)
        ]
        return matching[0] if len(matching) == 1 else None

    def stop_confirmation(self) -> Label | None:
        for notice in self.labels:
            message = re.sub(r"[^\w]", "", normalize(notice.text))
            if message not in _STOP_NOTICES:
                continue
            center_labels = [
                label for label in self.labels
                if abs(label.x - notice.x) < self.width / 4
                and abs(label.y - notice.y) < self.height / 3
            ]
            if any(word in normalize(label.text)
                   for label in center_labels for word in _DISALLOWED_CONFIRMATION):
                return None
            choices = [
                button for button in self.exact({"确定", "确认"})
                if notice.y < button.y < notice.y + self.height / 3
                and abs(button.x - notice.x) < self.width / 4
            ]
            cancel = any(
                abs(label.y - choice.y) <= max(label.height, choice.height)
                and abs(label.x - choice.x) < self.width / 3
                for label in self.exact({"取消"}) for choice in choices
            )
            if len(choices) == 1 and cancel:
                return choices[0]
        return None


def executable_for_window(hwnd: int) -> Path | None:
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
    kernel32.OpenProcess.restype = wintypes.HANDLE
    handle = kernel32.OpenProcess(0x1000, False, pid)
    if not handle:
        return None
    try:
        size = wintypes.DWORD(32768)
        filename = ctypes.create_unicode_buffer(size.value)
        if kernel32.QueryFullProcessImageNameW(
            wintypes.HANDLE(handle), 0, filename, ctypes.byref(size)
        ):
            return Path(filename.value)
        return None
    finally:
        kernel32.CloseHandle(wintypes.HANDLE(handle))


def find_executable(explicit: Path | None) -> Path | None:
    if explicit is not None:
        if explicit.name.casefold() not in _CLIENTS or not explicit.is_file():
            raise BoostError("请用 --exe 指定已安装的 uu_launcher.exe 或 uu.exe")
        return explicit.resolve()
    for key in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        root = os.environ.get(key)
        if root:
            folder = Path(root) / "Netease" / "UU"
            for name in ("uu_launcher.exe", "uu.exe"):
                if (folder / name).is_file():
                    return folder / name
    return None


class DesktopClient:
    def __init__(self, exe: Path | None) -> None:
        ctypes.windll.user32.SetProcessDPIAware()
        try:
            import numpy
            import win32gui
            from comtypes import COMError
            from PIL import ImageGrab
            from pywinauto import Desktop, keyboard, mouse
            from pywintypes import error as Win32Error
            from rapidocr_onnxruntime import RapidOCR
        except ImportError as exc:
            raise BoostError("缺少 UU 控制依赖，请安装 pywinauto、rapidocr-onnxruntime 和 Pillow") from exc

        self.gui = win32gui
        self.desktop = Desktop
        self.keyboard = keyboard
        self.mouse = mouse
        self.numpy = numpy
        self.grab = ImageGrab.grab
        self.window_errors = (OSError, RuntimeError, COMError, Win32Error)
        self.recognize = RapidOCR(text_score=0.55)
        self.exe = find_executable(exe)
        self.window = None
        self.rect = None

    def attach(self, deadline: float) -> None:
        launched = False
        while time.monotonic() < deadline:
            matches = self._windows()
            if len(matches) > 1:
                raise BoostError("检测到多个 UU 客户端窗口，请只保留当前使用的客户端")
            if matches:
                self.window = matches[0]
                self._focus()
                return
            if not launched:
                if self.exe is None:
                    raise BoostError("找不到 UU 客户端窗口，请打开 UU 或配置 uu_launcher.exe 路径")
                subprocess.Popen(
                    [str(self.exe)], cwd=self.exe.parent, stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                launched = True
            time.sleep(0.6)
        raise BoostError("等待 UU 加速器窗口超时，请检查本机安装和登录状态")

    def _windows(self):
        matches = []
        for window in self.desktop(backend="win32").windows(visible_only=True):
            title = normalize(window.window_text())
            if not title.startswith(("uu加速器", "网易uu加速器", "uu网游加速器")):
                continue
            path = executable_for_window(window.handle)
            if path is None or path.name.casefold() not in _CLIENTS:
                continue
            if self.exe is not None and self.exe.parent not in path.parents:
                continue
            rect = window.rectangle()
            if window.is_minimized() or rect.width() >= 350 and rect.height() >= 250:
                matches.append(window)
        return matches

    def _focus(self) -> None:
        try:
            if self.window.is_minimized():
                self.window.restore()
            self.window.set_focus()
        except self.window_errors as exc:
            raise BoostError("无法恢复 UU 前台窗口，请检查窗口所在会话是否已解锁") from exc
        if self.gui.GetForegroundWindow() != self.window.handle:
            raise BoostError("UU 窗口未取得前台焦点，请保持 Windows 桌面解锁")

    def page(self) -> Page:
        self._focus()
        self.rect = self.window.rectangle()
        image = self.grab(
            (self.rect.left, self.rect.top, self.rect.right, self.rect.bottom),
            all_screens=True,
        )
        width, height = image.size
        labels = self._uia_labels(width, height)
        pixels = self.numpy.ascontiguousarray(
            self.numpy.asarray(image.convert("RGB"))[:, :, ::-1]
        )
        lines, _ = self.recognize(pixels)
        for box, text, _ in lines or []:
            xs, ys = zip(*box)
            labels.append(Label(text, (int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))))
        return Page(width, height, tuple(labels))

    def _uia_labels(self, width: int, height: int) -> list[Label]:
        try:
            window = self.desktop(backend="uia").window(handle=self.window.handle)
            controls = window.descendants()
        except self.window_errors:
            return []
        labels = []
        for control in controls:
            try:
                if not control.is_visible():
                    continue
                info = control.element_info
                if info.control_type not in {"Edit", "Button", "Text", "ListItem", "ComboBox"}:
                    continue
                rect = control.rectangle()
            except self.window_errors:
                continue
            relative = (
                rect.left - self.rect.left, rect.top - self.rect.top,
                rect.right - self.rect.left, rect.bottom - self.rect.top,
            )
            if 0 <= relative[0] < relative[2] <= width and 0 <= relative[1] < relative[3] <= height:
                labels.append(Label(info.name or "", relative, info.control_type))
        return labels

    def click(self, label: Label) -> None:
        self._focus()
        current = self.window.rectangle()
        if current != self.rect:
            raise BoostError("UU 窗口在识别后移动，请重试")
        point = (current.left + label.x, current.top + label.y)
        try:
            hit = self.gui.WindowFromPoint(point)
            if hit != self.window.handle and not self.gui.IsChild(self.window.handle, hit):
                raise BoostError("UU 控件被其他窗口遮挡，请重试")
            self.mouse.click(coords=point)
        except BoostError:
            raise
        except self.window_errors as exc:
            raise BoostError("无法点击 UU 控件，请检查窗口权限") from exc

    def enter_search(self, label: Label, query: str) -> None:
        self.click(label)
        if self.gui.GetForegroundWindow() != self.window.handle:
            raise BoostError("UU 搜索框未取得焦点")
        self.keyboard.send_keys("^a{BACKSPACE}")
        chars = {"{": "{{}", "}": "{}}", "(": "{(}", ")": "{)}",
                 "+": "{+}", "^": "{^}", "%": "{%}", "~": "{~}"}
        self.keyboard.send_keys(
            "".join(chars.get(char, char) for char in query),
            with_spaces=True, vk_packet=True,
        )


def boost(client: DesktopClient, game: str, query: str, region: str, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    client.attach(deadline)
    searched = False
    opened = False
    stopping = False
    stopped_dialog = False
    active_missing = 0
    ready_frames = 0
    start_clicked = False
    region_clicked = False
    region_chosen = False
    reason = "未找到已登录的 UU 游戏页面"

    while time.monotonic() < deadline:
        page = client.page()
        active = page.active_button()
        game_active = bool(active and page.titled_action(game, {"停止加速"}))
        field, region_matches = page.region_field(region) if region else (None, True)
        if page.has_confirmation():
            ready_frames = 0
            confirmation = page.stop_confirmation()
            if confirmation and not stopped_dialog and (stopping or opened or start_clicked):
                client.click(confirmation)
                stopped_dialog = True
            reason = "UU 显示了确认、登录或会员提示，请查看窗口"
        elif game_active and region_matches and not stopping:
            ready_frames += 1
            if ready_frames >= 2:
                return
        else:
            ready_frames = 0
            if stopping:
                if active:
                    active_missing = 0
                else:
                    active_missing += 1
                    stopping = active_missing < 2
                    if not stopping:
                        searched = opened = start_clicked = False
                        stopped_dialog = False
                        region_clicked = region_chosen = False
                reason = "旧加速会话未停止，请检查 UU 是否有弹窗"
            elif active and (not game_active or (field is not None and not region_matches)):
                client.click(active)
                stopping = True
                active_missing = 0
                reason = "等待旧加速会话停止"
            elif game_active:
                reason = f"未能验证当前区服为「{region}」"
            elif start_clicked:
                reason = "已请求加速，未观察到指定游戏和区服就绪"
            elif region_clicked and not region_chosen and (option := page.region_option(region)):
                client.click(option)
                region_chosen = True
            elif (start := page.titled_action(game, _START)):
                if region_matches:
                    client.click(start)
                    start_clicked = True
                elif not region_clicked and field:
                    client.click(field)
                    region_clicked = True
                reason = f"等待 UU 识别可用的加速按钮或区服「{region}」"
            elif not opened:
                search = page.search(query if searched else "")
                if search is not None and not searched:
                    client.enter_search(search, query)
                    searched = True
                elif search is not None and (result := page.search_result(search, game)):
                    client.click(result)
                    opened = True
                reason = f"未找到名称准确匹配「{game}」的搜索结果"
            else:
                reason = f"已打开「{game}」，未识别到加速控件"
        time.sleep(0.65)
    raise BoostError(f"{reason}。请在 UU 界面核对登录、卡片名称、区服和提示。")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", required=True, help="UU 搜索结果中完整的游戏卡片名称")
    parser.add_argument("--query", help="可选搜索词，默认使用 --game")
    parser.add_argument("--region", default="", help="可选的 UU 区服显示名称")
    parser.add_argument("--exe", type=Path, help="已安装的 uu_launcher.exe 或 uu.exe")
    parser.add_argument("--timeout", type=float, default=90, help="最多等待秒数（默认 90）")
    args = parser.parse_args(argv)
    if os.name != "nt":
        parser.error("UU 桌面控制仅支持 Windows")
    query = args.query if args.query is not None else args.game
    if any(not value.strip() or any(ord(char) < 32 for char in value) for value in (args.game, query)):
        parser.error("请输入非空的 UU 游戏名称和搜索词")
    if not 0 < args.timeout <= 600:
        parser.error("--timeout 必须在 0 到 600 秒之间")
    try:
        boost(DesktopClient(args.exe), args.game, query, args.region.strip(), args.timeout)
    except (OSError, RuntimeError) as exc:
        print(f"UU 加速未就绪，{exc}", file=sys.stderr)
        return 1
    print(f"UU 已加速「{args.game}」" + (f"「{args.region}」" if args.region else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
