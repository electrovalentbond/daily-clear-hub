import logging
import unittest

from core.config_loader import GameConfig, HubConfig, SchedulerConfig
from core.scheduler import CallableGameRunner, DailyScheduler


class TestScheduler(unittest.TestCase):
    def test_run_all_executes_enabled_games_in_order(self):
        calls: list[tuple[str, list[str]]] = []

        def record(game_id: str, task_names: list[str]) -> None:
            calls.append((game_id, task_names))

        hub = HubConfig(
            schedule_order=["pcr", "honkai3"],
            scheduler=SchedulerConfig(max_retries=0, retry_delay_sec=0),
            games={
                "honkai3": GameConfig(enabled=True, tasks=["daily"]),
                "pcr": GameConfig(enabled=True, tasks=["daily"]),
                "genshin": GameConfig(enabled=False, tasks=["daily"]),
            },
        )
        scheduler = DailyScheduler(
            hub_config=hub,
            runner=CallableGameRunner(run_fn=record),
            log=logging.getLogger("test"),
        )

        report = scheduler.run_all()

        self.assertTrue(report.success)
        self.assertEqual(
            [("pcr", ["daily"]), ("honkai3", ["daily"])],
            calls,
        )

    def test_retry_on_failure(self):
        attempts = {"count": 0}

        def flaky(_game_id: str, _task_names: list[str]) -> None:
            attempts["count"] += 1
            if attempts["count"] < 2:
                raise RuntimeError("temporary")

        hub = HubConfig(
            schedule_order=["honkai3"],
            scheduler=SchedulerConfig(max_retries=2, retry_delay_sec=0),
            games={"honkai3": GameConfig(enabled=True, tasks=["daily"])},
        )
        scheduler = DailyScheduler(
            hub_config=hub,
            runner=CallableGameRunner(run_fn=flaky),
            log=logging.getLogger("test"),
        )

        report = scheduler.run_all()

        self.assertTrue(report.success)
        self.assertEqual(2, attempts["count"])


if __name__ == "__main__":
    unittest.main()
