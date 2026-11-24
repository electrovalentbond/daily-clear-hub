"""Run one AUTO-MAS task using the configured pcr-script installation."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


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

    with RunSession("daily"):
        config = load_config(args.config)
        groups = config.get("Task")
        rows = next(iter(groups.values())) if isinstance(groups, dict) and len(groups) == 1 else None
        if not isinstance(rows, list) or len(rows) != 1:
            raise ValueError("AUTO-MAS 的公主连结任务配置必须恰好包含一项任务")
        row = rows[0]
        task = row[0] if isinstance(row, list) and row and isinstance(row[0], str) else ""
        task_class = find_taskclass(task)
        if task_class is None:
            raise ValueError(f"未知的公主连结任务：{task}")

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
    print_report(report)


if __name__ == "__main__":
    main()
