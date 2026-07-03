from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Protocol

from core.config_loader import HubConfig, enabled_games_in_order, load_hub_config
from games.registry import GameRunContext, resolve_game_runner

logger = logging.getLogger(__name__)


class GameRunner(Protocol):
    def run_tasks(self, game_id: str, task_names: list[str]) -> None:
        ...


@dataclass
class RunResult:
    game_id: str
    task_name: str
    success: bool
    attempts: int
    error: str | None = None


@dataclass
class SchedulerReport:
    results: list[RunResult] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return all(result.success for result in self.results)


class DailyScheduler:
    def __init__(
        self,
        hub_config: HubConfig | None = None,
        runner: GameRunner | None = None,
        log: logging.Logger | None = None,
    ):
        self.hub_config = hub_config or load_hub_config()
        self.runner = runner or LoggingGameRunner(log or logger)
        self.log = log or logger

    def run_all(self) -> SchedulerReport:
        report = SchedulerReport()
        for game_id, game in enabled_games_in_order(self.hub_config):
            self.log.info("开始游戏日常: %s (%s)", game_id, ", ".join(game.tasks))
            for task_name in game.tasks:
                result = self._run_with_retry(game_id, task_name)
                report.results.append(result)
                if not result.success:
                    self.log.error(
                        "任务失败: %s/%s, error=%s",
                        game_id,
                        task_name,
                        result.error,
                    )
        return report

    def _run_with_retry(self, game_id: str, task_name: str) -> RunResult:
        scheduler = self.hub_config.scheduler
        last_error: str | None = None

        for attempt in range(1, scheduler.max_retries + 2):
            try:
                self.runner.run_tasks(game_id, [task_name])
                return RunResult(
                    game_id=game_id,
                    task_name=task_name,
                    success=True,
                    attempts=attempt,
                )
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                self.log.warning(
                    "任务重试 %s/%s (%s/%d): %s",
                    game_id,
                    task_name,
                    attempt,
                    scheduler.max_retries + 1,
                    exc,
                )
                if attempt <= scheduler.max_retries:
                    time.sleep(scheduler.retry_delay_sec)

        return RunResult(
            game_id=game_id,
            task_name=task_name,
            success=False,
            attempts=scheduler.max_retries + 1,
            error=last_error,
        )


class LoggingGameRunner:
    def __init__(self, log: logging.Logger | None = None):
        self.log = log or logger

    def run_tasks(self, game_id: str, task_names: list[str]) -> None:
        for task_name in task_names:
            context = GameRunContext(game_id=game_id, task_name=task_name)
            runner = resolve_game_runner(context)
            if runner is None:
                raise RuntimeError(f"未注册 runner: {game_id}/{task_name}")
            self.log.info("执行 runner: %s", runner.describe())
            runner.run(context)


@dataclass
class CallableGameRunner:
    run_fn: Callable[[str, list[str]], None]

    def run_tasks(self, game_id: str, task_names: list[str]) -> None:
        self.run_fn(game_id, task_names)
