from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Protocol


class StepOutcome(Enum):
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True)
class DailyStep:
    step_id: str
    name: str
    handler: Callable[["FlowContext"], StepOutcome]


@dataclass
class StepReport:
    step_id: str
    name: str
    outcome: StepOutcome
    message: str = ""


@dataclass
class FlowReport:
    game_id: str
    steps: list[StepReport] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return all(step.outcome != StepOutcome.FAILED for step in self.steps)

    @property
    def completed_count(self) -> int:
        return sum(1 for step in self.steps if step.outcome == StepOutcome.SUCCESS)


class FlowContext(Protocol):
    def log(self, message: str) -> None:
        ...

    def warn(self, message: str) -> None:
        ...

    def sleep(self, seconds: float) -> None:
        ...

    def is_step_enabled(self, step_id: str) -> bool:
        ...

    def click_feature(self, name: str, *, timeout: float = 5) -> bool:
        ...

    def click_ocr(self, texts: list[str], *, timeout: float = 5) -> bool:
        ...

    def find_feature(self, name: str) -> bool:
        ...


class DailyFlow:
    def __init__(self, game_id: str, steps: list[DailyStep]):
        self.game_id = game_id
        self.steps = steps

    def run(self, ctx: FlowContext) -> FlowReport:
        report = FlowReport(game_id=self.game_id)
        for step in self.steps:
            if not ctx.is_step_enabled(step.step_id):
                report.steps.append(
                    StepReport(step.step_id, step.name, StepOutcome.SKIPPED, "配置已关闭")
                )
                continue

            ctx.log(f"开始: {step.name}")
            try:
                outcome = step.handler(ctx)
            except Exception as exc:  # noqa: BLE001 - flow boundary
                ctx.warn(f"{step.name} 异常: {exc}")
                report.steps.append(
                    StepReport(step.step_id, step.name, StepOutcome.FAILED, str(exc))
                )
                continue

            report.steps.append(StepReport(step.step_id, step.name, outcome))
            if outcome == StepOutcome.FAILED:
                ctx.warn(f"失败: {step.name}")
            elif outcome == StepOutcome.SKIPPED:
                ctx.warn(f"跳过: {step.name}")

        return report
