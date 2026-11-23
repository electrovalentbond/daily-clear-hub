from __future__ import annotations

from pathlib import PureWindowsPath

from ok import BaseTask

from games.rewards import Outcome


class DailyClearTask(BaseTask):
    def __init__(self, *args, **kwargs):  # 初始化 ok-script 一次性任务。
        super().__init__(*args, **kwargs)  # 继承框架的任务生命周期。
        self.name = "Daily Clear Hub"  # 为日志提供固定任务名。
        self.report = None  # 缺少完整报告时，运行入口将退出为失败。
        self.failure = None  # 保存具体失败原因供命令行读取。
        self.hwnd_at_start = None  # 跟踪本次运行首次确认的窗口。

    def run(self):  # 执行当前游戏选中的奖励页面。
        self.report = []  # 保存每个页面独立的执行结果。
        try:  # 将框架后台线程里的异常传给命令行。
            self.prepare_target()  # 按配置核对窗口或打开指定模拟器应用。
            for page in self.pages:  # 按本机配置定义的顺序处理页面。
                self.log_info(f"开始 {page.name}")  # 将进行中的页面写入日志。
                result = self.flow.run_page(self, page)  # 确认页面、领奖并返回主界面。
                self.report.append(result)  # 完整保留每一步的结果。
                if result.outcome == Outcome.FAILED:  # 识别失败也需要进入报告。
                    self.log_warning(f"{page.name} · {result.detail}")  # 记录没能确认的状态。
                else:  # 保留本页是否有奖励可领的区别。
                    self.log_info(f"{page.name} · {result.detail}")  # 记录已领完或确认为空。
        except Exception as exc:  # 交给框架保留异常堆栈。
            self.failure = str(exc) or type(exc).__name__  # 将简明原因传回命令行。
            raise  # 保留框架自己的停止和错误处理。

    def prepare_target(self):
        if self.platform == "adb":
            manager = self.executor.device_manager
            connected = {item.serial for item in manager.adb.device_list()}
            if connected != {self.adb_serial}:
                raise RuntimeError(f"请只保留已配置的 ADB 设备 {self.adb_serial} 在线")
            device = self.adb_device()
            if not self.is_game_in_front(device):
                if self.target not in device.list_packages():
                    raise RuntimeError(f"设备 {self.adb_serial} 未安装 {self.target}")
                device.app_start(self.target)
                if not self.wait_until(
                    lambda: self.is_game_in_front(self.adb_device()),
                    time_out=20,
                    post_action=lambda: self.sleep(0.3),
                ):
                    raise RuntimeError(f"未切到 {self.target}，请启动游戏并登录")
        self.verify_target()
        if self.platform == "windows":
            window = self.executor.device_manager.hwnd_window
            # 1.0.154 的无界面入口会跳过交互器的前台准备。
            if not window.is_foreground() and not window.bring_to_front():
                raise RuntimeError("无法激活游戏窗口，请保持桌面解锁并打开游戏")

    def adb_device(self):
        manager = self.executor.device_manager
        selected = manager.get_preferred_device()
        if not selected or selected.get("address") != self.adb_serial:
            raise RuntimeError(f"ok-script 未选中配置的 ADB 设备 {self.adb_serial}")
        device = manager.device
        if device is None or device.serial != self.adb_serial:
            raise RuntimeError(f"ADB 设备 {self.adb_serial} 未连接")
        return device

    def is_game_in_front(self, device):
        current = device.app_current()
        return current is not None and current.package == self.target

    def verify_target(self):
        if self.platform == "adb":
            if not self.is_game_in_front(self.adb_device()):
                raise RuntimeError(f"{self.target} 已离开前台，停止操作")
            return

        manager = self.executor.device_manager
        selected = manager.get_preferred_device() or {}
        executable = PureWindowsPath(selected.get("full_path") or "").name
        hwnd = manager.hwnd_window.hwnd
        if not hwnd or hwnd != selected.get("real_hwnd") or executable.casefold() != self.target.casefold():
            raise RuntimeError(f"无法确认 {self.target} 的窗口，请打开游戏")
        if self.hwnd_at_start is None:
            self.hwnd_at_start = hwnd
        elif hwnd != self.hwnd_at_start:
            raise RuntimeError("游戏窗口发生变化，停止操作")

    def wait_for(self, names, *, anchor=None, timeout=5):
        def detect():
            frame = self.frame
            if frame is None:
                raise RuntimeError("未获取游戏画面，请用 gui 检查截图")
            height, width = frame.shape[:2]
            if (width, height) != self.expected_resolution:
                raise RuntimeError(f"实际截图尺寸为 {width}×{height}，请调整为配置中的 resolution")
            if anchor and not self.find_one(anchor):
                return set()
            return {name for name in names if self.find_one(name)}

        return self.wait_until(detect, time_out=timeout, post_action=lambda: self.sleep(0.2)) or set()

    def click_feature(self, feature):
        target = self.find_one(feature)
        if not target:
            return False
        self.verify_target()
        return bool(self.click_box(target, after_sleep=0.4))

    def press(self, key):
        self.verify_target()
        if not self.send_key(key, after_sleep=0.4):
            raise RuntimeError(f"按键失败：{key}")
