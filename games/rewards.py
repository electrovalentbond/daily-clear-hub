from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

MAX_BACK_ACTIONS = 6
MAX_CLAIMS = 20


class Outcome(Enum):
    CLAIMED = "claimed"
    EMPTY = "empty"
    FAILED = "failed"


@dataclass(frozen=True)
class Key:
    name: str


@dataclass(frozen=True)
class RewardPage:
    step_id: str
    name: str
    route: tuple[tuple[str | Key, str], ...]
    claim: str
    empty: str


@dataclass(frozen=True)
class StepResult:
    step_id: str
    outcome: Outcome
    detail: str


class RewardContext(Protocol):
    def wait_for(self, names: tuple[str, ...], *, anchor: str | None = None, timeout: float = 5) -> set[str]:
        ...

    def click_feature(self, feature: str) -> bool:
        ...

    def press(self, key: str) -> None:
        ...


@dataclass(frozen=True)
class RewardFlow:
    game_id: str
    home: str
    back: str
    popup: str
    pages: tuple[RewardPage, ...]

    def select(self, step_ids: tuple[str, ...]) -> tuple[RewardPage, ...]:
        pages = {page.step_id: page for page in self.pages}
        unknown = set(step_ids) - pages.keys()
        if unknown:
            raise ValueError(f"{self.game_id} 有未知步骤：{', '.join(sorted(unknown))}")
        return tuple(pages[step_id] for step_id in step_ids)

    def required_features(self, pages: tuple[RewardPage, ...]) -> set[str]:
        required = {self.home, self.back, self.popup}
        for page in pages:
            required.update((page.claim, page.empty))
            for entry, marker in page.route:
                required.add(marker)
                if isinstance(entry, str):
                    required.add(entry)
        return required

    def return_home(self, ctx: RewardContext) -> bool:
        for count in range(MAX_BACK_ACTIONS + 1):
            states = ctx.wait_for((self.popup, self.home, self.back), timeout=3)
            if self.popup not in states and self.home in states:
                return True
            action = self.popup if self.popup in states else self.back
            if count == MAX_BACK_ACTIONS or action not in states or not ctx.click_feature(action):
                return False
        return False

    def run_page(self, ctx: RewardContext, page: RewardPage) -> StepResult:
        if not self.return_home(ctx):
            return StepResult(page.step_id, Outcome.FAILED, f"无法确认主界面 {self.home}")
        result = self._claim(ctx, page)
        if not self.return_home(ctx):
            return StepResult(page.step_id, Outcome.FAILED, f"{result.detail}；无法确认返回主界面 {self.home}")
        return result

    def _claim(self, ctx: RewardContext, page: RewardPage) -> StepResult:
        preceding = self.home
        for entry, marker in page.route:
            if isinstance(entry, Key):
                if not ctx.wait_for((preceding,), timeout=3):
                    return StepResult(page.step_id, Outcome.FAILED, f"无法确认按键前的页面 {preceding}")
                ctx.press(entry.name)
            elif not ctx.wait_for((entry,), anchor=preceding) or not ctx.click_feature(entry):
                return StepResult(page.step_id, Outcome.FAILED, f"未找到页面入口 {entry}")
            if not ctx.wait_for((marker,)):
                return StepResult(page.step_id, Outcome.FAILED, f"未确认到达页面 {marker}")
            preceding = marker

        marker = page.route[-1][1]
        for count in range(MAX_CLAIMS + 1):
            states = ctx.wait_for((page.empty, page.claim, self.popup), anchor=marker)
            if self.popup in states:
                return StepResult(page.step_id, Outcome.FAILED, f"操作之前出现未预期的领奖弹窗 {self.popup}")
            if page.empty in states and page.claim in states:
                return StepResult(page.step_id, Outcome.FAILED, f"{page.claim} 与 {page.empty} 同时命中")
            if page.empty in states:
                outcome = Outcome.CLAIMED if count else Outcome.EMPTY
                detail = f"已领取并确认领完（{count} 次）" if count else "已确认暂无可领取奖励"
                return StepResult(page.step_id, outcome, detail)
            if count == MAX_CLAIMS or page.claim not in states or not ctx.click_feature(page.claim):
                return StepResult(page.step_id, Outcome.FAILED, f"未确认领完 {page.empty}，或无可操作的 {page.claim}")

            # 等到明确的领取反馈。按钮持续可见时不重复点击。
            result = ctx.wait_for((self.popup, page.empty))
            if self.popup in result:
                if not ctx.click_feature(self.popup):
                    return StepResult(page.step_id, Outcome.FAILED, f"无法关闭领奖弹窗 {self.popup}")
            elif page.empty not in result:
                return StepResult(page.step_id, Outcome.FAILED, f"点击 {page.claim} 后未观察到领取反馈")

        raise AssertionError("领取循环应在达到上限时结束")
