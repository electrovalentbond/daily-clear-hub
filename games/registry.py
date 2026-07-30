from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from games.adapters import MockFlowContext
from games.bhxy2.flow import BHXY2_DAILY_FLOW
from games.genshin.flow import GENSHIN_DAILY_FLOW
from games.honkai3.flow import HONKAI3_DAILY_FLOW
from games.pcr.flow import PCR_DAILY_FLOW
from games.starrail.flow import STARRAIL_DAILY_FLOW
from games.zzz.flow import ZZZ_DAILY_FLOW


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


def _windows_or_mock(task_name: str, flow, game_id: str) -> Callable[[GameRunContext], None]:
    def _runner(context: GameRunContext) -> None:
        try:
            from ok import run_task
            from src.config import config

            run_task(config, task_name=task_name)
        except ImportError:
            _run_flow_mock(flow, game_id)(context)

    return _runner


RUNNERS: dict[tuple[str, str], StepRunner] = {
    ("honkai3", "daily"): CallableStepRunner(
        "honkai3/daily",
        _windows_or_mock("Honkai3DailyTask", HONKAI3_DAILY_FLOW, "honkai3"),
    ),
    ("starrail", "daily"): CallableStepRunner(
        "starrail/daily",
        _windows_or_mock("StarRailDailyTask", STARRAIL_DAILY_FLOW, "starrail"),
    ),
    ("zzz", "daily"): CallableStepRunner(
        "zzz/daily",
        _windows_or_mock("ZzzDailyTask", ZZZ_DAILY_FLOW, "zzz"),
    ),
    ("genshin", "daily"): CallableStepRunner(
        "genshin/daily",
        _windows_or_mock("GenshinDailyTask", GENSHIN_DAILY_FLOW, "genshin"),
    ),
    ("pcr", "daily"): CallableStepRunner(
        "pcr/daily",
        _windows_or_mock("PcrDailyTask", PCR_DAILY_FLOW, "pcr"),
    ),
    ("bhxy2", "daily"): CallableStepRunner(
        "bhxy2/daily",
        _windows_or_mock("Bhxy2DailyTask", BHXY2_DAILY_FLOW, "bhxy2"),
    ),
}


def resolve_game_runner(context: GameRunContext) -> StepRunner | None:
    return RUNNERS.get((context.game_id, context.task_name))
