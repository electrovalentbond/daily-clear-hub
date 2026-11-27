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
_GA_ROOTOWNER = 3
_SEARCH_LABELS = {"搜索", "搜索游戏", "搜索游戏/应用", "搜索对应游戏名", "请输入游戏名称", "搜索游戏名称"}
_START = {"开始加速", "立即加速", "一键加速"}
_LAUNCH = {"启动游戏"}
_REGION_LABELS = {"游戏服", "区服", "游戏区服", "加速区服", "选择区服"}
_STOP_NOTICES = {
    "重新加速将断开正在加速游戏连接",
    "停止加速将断开当前游戏连接",
    "停止加速后当前游戏将断开连接",
    "其他游戏正在加速",
}
_STOP_QUESTIONS = {"确定停止加速吗", "确定要停止加速吗", "确认停止加速吗", "是否停止加速"}
_DISALLOWED_CONFIRMATION = ("付费", "购买", "充值", "开通", "支付", "订阅", "扣费")


class BoostError(RuntimeError):
    pass


def normalize(text: str) -> str:
    return "".join(unicodedata.normalize("NFKC", text).casefold().split())


def _stop_notice_text(text: str) -> str:
    return re.sub(r"[^\w]", "", normalize(text))


@dataclass(frozen=True)
class Label:
    text: str
    rect: tuple[int, int, int, int]
    role: str = ""
    enabled: bool | None = None

    @property
    def x(self) -> int:
        return (self.rect[0] + self.rect[2]) // 2

    @property
    def y(self) -> int:
        return (self.rect[1] + self.rect[3]) // 2

    @property
    def height(self) -> int:
        return self.rect[3] - self.rect[1]


def point(text: str, x: int, y: int) -> Label:
    return Label(text, (x, y, x + 1, y + 1))


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

    def _navigation_row(self) -> Label | None:
        homes = [
            home for home in self.exact({"首页"})
            if home.x < self.width / 3 and home.y < self.height / 6
            and any(
                home.x < tab.x < self.width / 2
                and abs(home.y - tab.y) <= home.height
                for tab in self.exact({"游戏"})
            )
        ]
        return homes[0] if len(homes) == 1 else None

    def search(self, query: str) -> Label | None:
        navigation = self._navigation_row()

        def in_search_bar(label: Label) -> bool:
            if navigation is None:
                return label.y < self.height / 4
            return (
                self.width * 0.68 < label.x < self.width * 0.92
                and abs(label.y - navigation.y) <= max(label.height, navigation.height)
            )

        edits = [
            label for label in self.labels
            if label.role == "Edit" and in_search_bar(label)
        ]
        if len(edits) == 1:
            return edits[0]
        names = _SEARCH_LABELS | {query}
        # OCR can read the magnifying-glass icon as "Q" before the text.
        names |= {"q" + normalize(name) for name in names}
        options = [
            label for label in self.exact(names)
            if in_search_bar(label)
        ]
        if len(options) == 1:
            return options[0]
        if navigation and not edits and not options:
            # The custom-drawn field remains on the right of the main tabs,
            # including when it contains a previous game's search text.
            return point("搜索", round(self.width * 0.82), navigation.y)
        return None

    def _results_heading(self) -> Label | None:
        for heading in self.exact({"搜索结果"}):
            if heading.x >= self.width / 4 or heading.y >= self.height / 3:
                continue
            if any(
                heading.rect[2] < label.x < self.width * 0.75
                and abs(label.y - heading.y) <= heading.height
                and re.fullmatch(r"共\d+个搜索结果", normalize(label.text))
                for label in self.labels
            ):
                return heading
        return None

    def search_result(self, search: Label | None, game: str) -> Label | None:
        heading = self._results_heading()
        if heading:
            cards = [
                label for label in self.exact({game})
                if label.x > self.width / 4 and label.y > heading.y + 4 * heading.height
            ]
            if len(cards) == 1:
                card = cards[0]
                # The full results page puts the title below the clickable cover.
                return point(card.text, card.x, card.y - 3 * card.height)
            return None
        if search is None:
            return None
        # Search suggestions are anchored to the search box. The search text
        # itself and a same-name tile elsewhere in the library are separate.
        options = [
            label for label in self.exact({game})
            if search.rect[3] <= label.y < search.y + self.height / 2
            and abs(label.x - search.x) < self.width / 4
        ]
        return options[0] if len(options) == 1 else None

    def home_card(self, game: str) -> Label | None:
        if self._navigation_row() is None or not any(
            label.y > self.height * 0.73
            and re.fullmatch(r"我的游戏(?:\(\d+\))?", normalize(label.text))
            for label in self.labels
        ):
            return None
        cards = [
            label for label in self.exact({game})
            if self.height * 0.50 < label.y < self.height * 0.73
        ]
        return cards[0] if len(cards) == 1 else None

    def home_start(self, card: Label) -> Label | None:
        buttons = [
            button for button in self.exact(_START)
            if 0 < card.y - button.y < self.height / 5
            and abs(button.x - card.x) < self.width / 10
        ]
        return buttons[0] if len(buttons) == 1 else None

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
        indicators = self.exact(_LAUNCH | {"游戏延迟", "丢包率", "网络监控"})
        return buttons[0] if len(buttons) == 1 and indicators else None

    def launch_button(self, active: Label) -> tuple[Label | None, str]:
        # The active stop button has already been matched to the game title.
        buttons = [
            button for button in self.exact(_LAUNCH)
            if abs(button.x - active.x) < self.width / 4
            and abs(button.y - active.y) <= max(button.height, active.height)
        ]
        if not buttons:
            return None, "未识别到加速详情页上的「启动游戏」按钮"
        if len(buttons) > 1:
            return None, "加速详情页有多个「启动游戏」按钮"
        button = buttons[0]
        # UIA and OCR can report separate labels for the same button.
        disabled = any(
            label.enabled is False and normalize(label.text) in _LAUNCH
            and abs(label.x - button.x) <= max(label.height, button.height)
            and abs(label.y - button.y) <= min(label.height, button.height)
            for label in self.labels
        )
        return (None, "「启动游戏」按钮不可用") if disabled else (button, "")

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

    def stop_notices(self) -> list[Label]:
        recognized = {
            label.text for label in self.labels
            if _stop_notice_text(label.text) in _STOP_NOTICES | _STOP_QUESTIONS
        }
        return [
            notice for notice in self.exact(recognized)
            if self.width * 0.30 < notice.x < self.width * 0.70
            and self.height / 3 < notice.y < self.height * 0.70
        ]

    def stop_confirmation(
        self, notices: list[Label], *, requested: bool,
    ) -> tuple[Label, Label] | None:
        choices = {"确定", "确认"}
        if requested:
            choices.update({"停止加速", "确认停止"})
        pairs = set()
        for notice in notices:
            if not requested and _stop_notice_text(notice.text) not in _STOP_NOTICES:
                continue
            center_labels = [
                label for label in self.labels
                if abs(label.x - notice.x) < self.width / 4
                and abs(label.y - notice.y) < self.height / 3
            ]
            if any(word in normalize(label.text)
                   for label in center_labels for word in _DISALLOWED_CONFIRMATION):
                return None
            pairs.update(
                (confirm, cancel)
                for confirm in self.exact(choices) for cancel in self.exact({"取消"})
                if notice.rect[3] <= min(confirm.y, cancel.y)
                and max(confirm.y, cancel.y) < notice.y + self.height / 3
                and min(confirm.x, cancel.x) < notice.x < max(confirm.x, cancel.x)
                and max(abs(confirm.x - notice.x), abs(cancel.x - notice.x)) < self.width / 4
                and abs(cancel.y - confirm.y) <= max(cancel.height, confirm.height)
            )
        return next(iter(pairs)) if len(pairs) == 1 else None


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
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        self.get_ancestor = user32.GetAncestor
        self.get_ancestor.argtypes = (wintypes.HWND, wintypes.UINT)
        self.get_ancestor.restype = wintypes.HWND
        try:
            import numpy
            import win32gui
            from comtypes import COMError
            from PIL import ImageGrab
            from pywinauto import Desktop, keyboard, mouse
            from win32process import GetWindowThreadProcessId
            from pywintypes import error as Win32Error
            from rapidocr_onnxruntime import RapidOCR
        except ImportError as exc:
            raise BoostError("缺少 UU 控制依赖，请安装 pywinauto、rapidocr-onnxruntime 和 Pillow") from exc

        self.gui = win32gui
        self.window_thread_process = GetWindowThreadProcessId
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
        handles = {window.handle for window in matches}
        return [
            window for window in matches
            if self.get_ancestor(window.handle, _GA_ROOTOWNER) not in handles - {window.handle}
        ]

    def _belongs_to_uu(self, hwnd: int) -> bool:
        main = self.window.handle
        if hwnd == main:
            return True
        if not hwnd or not (
            self.gui.IsChild(main, hwnd) or self.get_ancestor(hwnd, _GA_ROOTOWNER) == main
        ):
            return False
        _, pid = self.window_thread_process(hwnd)
        return bool(pid and pid == self.window_thread_process(main)[1])

    def _focus(self) -> None:
        try:
            if self.window.is_minimized():
                self.window.restore()
            if not self._belongs_to_uu(self.gui.GetForegroundWindow()):
                self.window.set_focus()
            focused = self._belongs_to_uu(self.gui.GetForegroundWindow())
        except self.window_errors as exc:
            raise BoostError("无法恢复 UU 前台窗口，请检查窗口所在会话是否已解锁") from exc
        if not focused:
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
                text = info.name or ""
                enabled = None
                if info.control_type == "Button" and normalize(text) in _LAUNCH:
                    enabled = bool(control.is_enabled())
            except self.window_errors:
                continue
            relative = (
                rect.left - self.rect.left, rect.top - self.rect.top,
                rect.right - self.rect.left, rect.bottom - self.rect.top,
            )
            if 0 <= relative[0] < relative[2] <= width and 0 <= relative[1] < relative[3] <= height:
                labels.append(Label(text, relative, info.control_type, enabled))
        return labels

    def _point(self, label: Label) -> tuple[int, int]:
        self._focus()
        current = self.window.rectangle()
        if current != self.rect:
            raise BoostError("UU 窗口在识别后移动，请重试")
        point = (current.left + label.x, current.top + label.y)
        hit = self.gui.WindowFromPoint(point)
        if not self._belongs_to_uu(hit):
            raise BoostError("UU 控件被其他窗口遮挡，请重试")
        return point

    def click(self, label: Label) -> None:
        try:
            self.mouse.click(coords=self._point(label))
        except BoostError:
            raise
        except self.window_errors as exc:
            raise BoostError("无法点击 UU 控件，请检查窗口权限") from exc

    def hover(self, label: Label) -> None:
        self.mouse.move(coords=self._point(label))

    def enter_search(self, label: Label, query: str) -> None:
        self.click(label)
        time.sleep(0.25)
        if self.gui.GetForegroundWindow() != self.window.handle:
            raise BoostError("UU 搜索框未取得焦点")
        self.keyboard.send_keys("^a{BACKSPACE}")
        chars = {"{": "{{}", "}": "{}}", "(": "{(}", ")": "{)}",
                 "+": "{+}", "^": "{^}", "%": "{%}", "~": "{~}"}
        self.keyboard.send_keys(
            "".join(chars.get(char, char) for char in query),
            with_spaces=True, vk_packet=True,
        )


def boost(
    client: DesktopClient, game: str, query: str, region: str, timeout: float,
    *, launch_game: bool = False,
) -> None:
    deadline = time.monotonic() + timeout
    client.attach(deadline)
    print("已连接 UU 窗口", flush=True)
    search_attempts = 0
    search_again_at = 0.0
    home_hovered = False
    opened = False
    stopping = False
    stopped_dialog = False
    active_missing = 0
    ready_frames = 0
    start_clicked = False
    region_clicked = False
    region_chosen = False
    reason = "未找到已登录的 UU 游戏页面"

    while (now := time.monotonic()) < deadline:
        page = client.page()
        active = page.active_button()
        game_active = page.titled_action(game, {"停止加速"}) if active else None
        field, region_matches = page.region_field(region) if region else (None, True)
        needs_stop = bool(active and (not game_active or (field is not None and not region_matches)))
        stop_notices = page.stop_notices()
        if stop_notices or page.has_confirmation():
            ready_frames = 0
            stop_controls = page.stop_confirmation(stop_notices, requested=stopping)
            if stop_controls and not stopped_dialog:
                confirm, cancel = stop_controls
                if stopping or needs_stop or ((opened or start_clicked) and not game_active):
                    client.click(confirm)
                    print("已确认停止 UU 的旧加速", flush=True)
                    stopping = stopping or needs_stop
                    active_missing = 0
                    stopped_dialog = True
                elif game_active and region_matches:
                    client.click(cancel)
                    print("已取消停止加速，继续使用当前 UU 会话", flush=True)
                    stopped_dialog = True
            reason = ("UU 的停止加速确认仍显示，请检查窗口" if stop_notices
                      else "UU 显示了确认、登录或会员提示，请查看窗口")
        elif game_active and region_matches and not stopping:
            ready_frames += 1
            if ready_frames >= 2:
                if not launch_game:
                    return
                if ready_frames == 2:
                    print(f"UU 已确认「{game}」加速就绪，准备启动游戏", flush=True)
                launch, problem = page.launch_button(game_active)
                if launch:
                    try:
                        client.click(launch)
                    except BoostError as exc:
                        raise BoostError(f"已识别「{game}」的「启动游戏」，点击失败：{exc}") from exc
                    print("已点击 UU 的「启动游戏」", flush=True)
                    return
                reason = f"「{game}」已加速，{problem}"
        else:
            ready_frames = 0
            if stopping:
                if active:
                    active_missing = 0
                else:
                    active_missing += 1
                    stopping = active_missing < 2
                    if not stopping:
                        search_attempts = 0
                        search_again_at = 0.0
                        home_hovered = opened = start_clicked = False
                        stopped_dialog = False
                        region_clicked = region_chosen = False
                reason = "旧加速会话未停止，请检查 UU 是否有弹窗"
            elif active and needs_stop:
                client.click(active)
                print("已请求停止 UU 的当前加速", flush=True)
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
                    print(f"已请求加速「{game}」", flush=True)
                    start_clicked = True
                elif not region_clicked and field:
                    client.click(field)
                    region_clicked = True
                reason = f"等待 UU 识别可用的加速按钮或区服「{region}」"
            elif not opened:
                card = page.home_card(game) if not region and not search_attempts else None
                search = page.search(query)
                if card and (button := page.home_start(card)):
                    client.click(button)
                    print(f"已从 UU 首页请求加速「{game}」", flush=True)
                    start_clicked = True
                    reason = "已请求加速，未观察到指定游戏就绪"
                elif card and not home_hovered:
                    client.hover(point(card.text, card.x, card.y - 4 * card.height))
                    home_hovered = True
                    reason = f"已识别 UU 首页的「{game}」，未识别到加速按钮"
                elif (result := page.search_result(search if search_attempts else None, game)):
                    client.click(result)
                    print(f"已选择 UU 同名游戏「{game}」", flush=True)
                    opened = True
                    reason = f"已选择「{game}」，未识别到加速控件"
                elif search is not None:
                    if search_attempts < 3 and now >= search_again_at:
                        client.enter_search(search, query)
                        search_attempts += 1
                        search_again_at = now + 4
                        print(f"正在搜索 UU 游戏「{query}」（第 {search_attempts} 次）", flush=True)
                    reason = f"已搜索「{query}」，未识别到唯一的同名游戏「{game}」"
                elif not search_attempts:
                    reason = "未识别到 UU 搜索框"
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
    parser.add_argument("--launch-game", action="store_true", help="加速就绪后点击 UU 的启动游戏")
    args = parser.parse_args(argv)
    if os.name != "nt":
        parser.error("UU 桌面控制仅支持 Windows")
    query = args.query if args.query is not None else args.game
    if any(not value.strip() or any(ord(char) < 32 for char in value) for value in (args.game, query)):
        parser.error("请输入非空的 UU 游戏名称和搜索词")
    if not 0 < args.timeout <= 600:
        parser.error("--timeout 必须在 0 到 600 秒之间")
    try:
        boost(
            DesktopClient(args.exe), args.game, query, args.region.strip(), args.timeout,
            launch_game=args.launch_game,
        )
    except (OSError, RuntimeError) as exc:
        failure = "UU 加速或启动失败" if args.launch_game else "UU 加速未就绪"
        print(f"{failure}，{exc}", file=sys.stderr)
        return 1
    print(f"UU 已加速「{args.game}」" + (f"「{args.region}」" if args.region else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
