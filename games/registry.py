from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from games.adapters import MockFlowContext
from games.honkai3.flow import HONKAI3_DAILY_FLOW
from games.pcr.flow import PCR_DAILY_FLOW


@dataclass(frozen=True)
class GameRunContext:
    game_id: str
    task_name: str


class StepRunner(Protocol):
    def describe(self) -> str:
        ...

    def run(self, context: GameRunContext) -> None:
        ...


@dataclass
class CallableStepRunner:
    label: str
    fn: Callable[[GameRunContext], None]

    def describe(self) -> str:
        return self.label

    def run(self, context: GameRunContext) -> None:
        self.fn(context)


def _run_flow_mock(flow, game_id: str) -> Callable[[GameRunContext], None]:
    def _runner(context: GameRunContext) -> None:
        mock = MockFlowContext(enabled_steps={step.step_id for step in flow.steps})
        report = flow.run(mock)
        if not report.success:
            failed = [s.name for s in report.steps if s.outcome.value == "failed"]
            raise RuntimeError(f"{game_id} 日常失败: {', '.join(failed)}")

    return _runner


def _honkai3_daily(context: GameRunContext) -> None:
    _run_flow_mock(HONKAI3_DAILY_FLOW, "honkai3")(context)


def _pcr_daily(context: GameRunContext) -> None:
    _run_flow_mock(PCR_DAILY_FLOW, "pcr")(context)


def _honkai3_daily_windows(context: GameRunContext) -> None:
    """Windows 上通过 ok-script 执行完整 Task（含截图识别）。"""
    try:
        from ok import run_task
        from src.config import config

        run_task(config, task_name="Honkai3DailyTask")
    except ImportError:
        _honkai3_daily(context)


def _pcr_daily_windows(context: GameRunContext) -> None:
    try:
        from ok import run_task
        from src.config import config

        run_task(config, task_name="PcrDailyTask")
    except ImportError:
        _pcr_daily(context)


RUNNERS: dict[tuple[str, str], StepRunner] = {
    ("honkai3", "daily"): CallableStepRunner("honkai3/daily", _honkai3_daily_windows),
    ("pcr", "daily"): CallableStepRunner("pcr/daily", _pcr_daily_windows),
}


def resolve_game_runner(context: GameRunContext) -> StepRunner | None:
    return RUNNERS.get((context.game_id, context.task_name))
