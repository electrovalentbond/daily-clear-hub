from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class TaskLike(Protocol):
    def log_info(self, message: str, notify: bool = False) -> None:
        ...

    def log_warning(self, message: str, notify: bool = False) -> None:
        ...

    def sleep(self, seconds: float, **kwargs: Any) -> None:
        ...

    def find_one(self, name: str, **kwargs: Any) -> Any:
        ...

    def wait_feature(self, name: str, time_out: float = 5, **kwargs: Any) -> Any:
        ...

    def click_box(self, box: Any, after_sleep: float = 0, **kwargs: Any) -> None:
        ...

    def wait_ocr(self, match: list[str] | str, time_out: float = 5, **kwargs: Any) -> Any:
        ...

    def click_relative(self, x: float, y: float, after_sleep: float = 0, **kwargs: Any) -> None:
        ...


@dataclass
class MockFlowContext:
    """macOS 单测用：记录步骤调用，不依赖 Win32/ok-script。"""

    enabled_steps: set[str] = field(default_factory=set)
    feature_hits: dict[str, bool] = field(default_factory=dict)
    ocr_hits: dict[str, bool] = field(default_factory=dict)
    default_feature_present: bool = True
    default_ocr_present: bool = True
    logs: list[str] = field(default_factory=list)
    clicks: list[str] = field(default_factory=list)

    def log(self, message: str) -> None:
        self.logs.append(message)

    def warn(self, message: str) -> None:
        self.logs.append(f"WARN: {message}")

    def sleep(self, seconds: float) -> None:
        self.logs.append(f"SLEEP {seconds}")

    def is_step_enabled(self, step_id: str) -> bool:
        return step_id in self.enabled_steps

    def _feature_present(self, name: str) -> bool:
        if name in self.feature_hits:
            return self.feature_hits[name]
        return self.default_feature_present

    def click_feature(self, name: str, *, timeout: float = 5) -> bool:
        if self._feature_present(name):
            self.clicks.append(f"feature:{name}")
            return True
        return False

    def click_ocr(self, texts: list[str], *, timeout: float = 5) -> bool:
        key = "|".join(texts)
        present = self.ocr_hits[key] if key in self.ocr_hits else self.default_ocr_present
        if present:
            self.clicks.append(f"ocr:{key}")
            return True
        return False

    def find_feature(self, name: str) -> bool:
        return self._feature_present(name)


class OkScriptFlowContext:
    """将 ok-script GameTask 适配为 FlowContext。"""

    def __init__(self, task: TaskLike, step_config: dict[str, bool]):
        self.task = task
        self.step_config = step_config

    def log(self, message: str) -> None:
        self.task.log_info(message)

    def warn(self, message: str) -> None:
        self.task.log_warning(message)

    def sleep(self, seconds: float) -> None:
        self.task.sleep(seconds)

    def is_step_enabled(self, step_id: str) -> bool:
        return bool(self.step_config.get(step_id, True))

    def click_feature(self, name: str, *, timeout: float = 5) -> bool:
        box = self.task.wait_feature(name, time_out=timeout)
        if box:
            self.task.click_box(box, after_sleep=0.8)
            return True
        self.warn(f"未找到模板: {name}")
        return False

    def click_ocr(self, texts: list[str], *, timeout: float = 5) -> bool:
        box = self.task.wait_ocr(match=texts, time_out=timeout)
        if box:
            self.task.click_box(box, after_sleep=0.8)
            return True
        self.warn(f"未找到文字: {texts}")
        return False

    def find_feature(self, name: str) -> bool:
        return bool(self.task.find_one(name))
