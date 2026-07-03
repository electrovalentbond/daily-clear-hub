import logging

from qfluentwidgets import FluentIcon

from core.scheduler import DailyScheduler
from src.tasks.MyBaseTask import MyBaseTask


class DailyClearTask(MyBaseTask):
    """一键执行已启用游戏的日常队列。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "一键清日常"
        self.description = "按 config.yaml 顺序执行各游戏已启用的日常任务"
        self.icon = FluentIcon.PLAY

    def run(self):
        scheduler = DailyScheduler(log=logging.getLogger("daily_clear_hub"))
        report = scheduler.run_all()
        if report.success:
            self.log_info("全部日常任务执行完成", notify=True)
        else:
            failed = [f"{r.game_id}/{r.task_name}" for r in report.results if not r.success]
            self.log_error(f"部分任务失败: {', '.join(failed)}", notify=True)
