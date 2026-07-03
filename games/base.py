from __future__ import annotations

from games.adapters import OkScriptFlowContext
from games.flow import DailyFlow, FlowReport
from src.tasks.MyBaseTask import MyBaseTask


class GameTask(MyBaseTask):
    """各游戏 Task 的基类。"""

    game_id: str = ""

    def log_step(self, message: str) -> None:
        self.log_info(f"[{self.game_id}] {message}")

    def build_step_config(self) -> dict[str, bool]:
        return {}

    def run_daily_flow(self, flow: DailyFlow) -> FlowReport:
        ctx = OkScriptFlowContext(self, self.build_step_config())
        report = flow.run(ctx)
        self.log_info(
            f"完成 {report.completed_count}/{len(report.steps)} 步",
            notify=True,
        )
        if not report.success:
            failed = [step.name for step in report.steps if step.outcome.value == "failed"]
            self.log_warning(f"失败步骤: {', '.join(failed)}")
        return report
