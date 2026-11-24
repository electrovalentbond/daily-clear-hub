"""Run one AUTO-MAS task using the configured pcr-script installation."""

from __future__ import annotations

import argparse
import subprocess
import sys
from importlib import import_module
from pathlib import Path


HUB_TASK_CLASSES = {
    "claim_alchemy_reward": ("core.pcr_alchemy_reward", "ClaimAlchemyReward"),
    "claim_gourmet_rewards": ("core.pcr_gourmet_rewards", "ClaimGourmetRewards"),
    "sweep_revival_hard": ("core.pcr_revival_sweep", "SweepRevivalHard"),
    "sweep_very_hard_boss": ("core.pcr_vh_sweep", "SweepVeryHardBoss"),
}


def restore_schedule_counter(task, screen):
    """Find the saved schedule counter, including below the notification rows."""
    from pcrscript.game_ui.screen import EventUIError

    track = (769, 97, 784, 445)
    content = (195, 97, 765, 445)

    def counter_visible(view):
        return task.book(view) and task.completion(view) is not None

    def scroll(view, direction):
        # Try the list body for an overlapping scan, then the thumb if the
        # game ignored that gesture while returning from the result screen.
        for distance in (220, None):
            try:
                return task.ui.scrollbar(
                    view, track, direction, reached=counter_visible,
                    content_distance=distance, content_roi=content,
                )
            except EventUIError as error:
                if str(error) != "列表后台滑动未生效":
                    raise
                view = task.ui.last if task.ui.last is not None else view
                if counter_visible(view):
                    return True
                if not task.book(view) or task.ui.scrollbar_bounds(view, track) is None:
                    break
        # A transient lock during settlement is not a failed schedule. The
        # upstream task will keep polling and only finish on verified counts.
        return None

    # Completion results can leave the book scrolled down. Start by looking
    # upward, then scan down with overlapping views of the list.
    for direction in (-1, 1):
        for _ in range(6):
            if not task.book(screen) or task.completion(screen) is not None:
                return screen
            if task.ui.scrollbar_bounds(screen, track) is None:
                return screen
            moved = scroll(screen, direction)
            if task.ui.last is not None:
                screen = task.ui.last
            if moved is None:
                return screen
            if not moved:
                break
    return screen


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="运行一项公主连结日常")
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args(argv)

    # The launcher sets cwd to the pinned pcr-script directory. Its own
    # interpreter and working directory also supply dependencies and assets.
    sys.path.insert(0, str(Path.cwd()))
    from pcrscript.driver import ADBDriver
    from pcrscript.run_session import RunSession, daily_result
    from pcrscript.runtime import load_config, print_report, run_script, select_driver, summarize_daily
    from pcrscript.tasks import TimeLimitTask, find_taskclass

    exit_status = None
    with RunSession("daily"):
        config = load_config(args.config)
        groups = config.get("Task")
        rows = next(iter(groups.values())) if isinstance(groups, dict) and len(groups) == 1 else None
        if not isinstance(rows, list) or len(rows) != 1:
            raise ValueError("AUTO-MAS 的公主连结任务配置必须恰好包含一项任务")
        row = rows[0]
        task = row[0] if isinstance(row, list) and row and isinstance(row[0], str) else ""
        if task in HUB_TASK_CLASSES:
            from pcrscript.tasks import register

            module, class_name = HUB_TASK_CLASSES[task]
            register(task, requires_home=True)(getattr(import_module(module), class_name))
        task_class = find_taskclass(task)
        if task_class is None:
            raise ValueError(f"未知的公主连结任务：{task}")
        if task == "schedule":
            # This process runs a single task from the pinned pcr-script.
            # Keep its submission, resource checks and completion verification.
            task_class.restore_counter = restore_schedule_counter

        extra = config.get("Extra")
        serial = extra.get("adb_serial") if isinstance(extra, dict) else None
        if not isinstance(serial, str) or not serial.strip():
            raise ValueError("AUTO-MAS 的公主连结任务必须绑定一个 ADB 设备")
        driver = select_driver(config)
        if not isinstance(driver, ADBDriver) or driver.device_name != serial.strip():
            raise ValueError("pcr-script 未使用 AUTO-MAS 绑定的 ADB 设备")
        subprocess.run(
            [driver.adb_path, "-s", driver.device_name, "shell", "monkey", "-p", "com.bilibili.priconne", "1"],
            stdin=subprocess.DEVNULL,
            check=True,
            timeout=15,
        )

        # run_script waits for the home screen before running the selected task.
        report = run_script(config)
        if (
            report.get("tasks") == []
            and report.get("status") == "finished"
            and report.get("verified") is False
            and issubclass(task_class, TimeLimitTask)
        ):
            report = summarize_daily([{
                "task": task,
                "status": "unavailable",
                "report": {"reason": "当前条件下不可执行此限时任务"},
            }])
            daily_result(report)

        # RunSession can exit with code 1 after a caught task error. Emit the
        # report first, while keeping print_report's exit outside the session.
        try:
            print_report(report)
        except SystemExit as exc:
            exit_status = exc
    if exit_status is not None:
        raise exit_status


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    main()
