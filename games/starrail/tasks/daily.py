from games.base import GameTask
from games.starrail.flow import DEFAULT_STEP_TOGGLES, STARRAIL_DAILY_FLOW, STEP_LABELS
from games.task_config import build_step_config


class StarRailDailyTask(GameTask):
    game_id = "starrail"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "星铁 日常"
        self.description = (
            "委托、消耗开拓力、每日实训、邮件等 MVP 日常。"
            "参考三月七小助手任务拆分，Windows 联调时需补充 assets 模板图。"
        )
        self.default_config.update(
            {label: DEFAULT_STEP_TOGGLES[step_id] for step_id, label in STEP_LABELS.items()}
        )
        self.config_description.update(
            {label: f"是否执行「{label}」" for label in STEP_LABELS.values()}
        )

    def build_step_config(self) -> dict[str, bool]:
        return build_step_config(self.config, STEP_LABELS)

    def run(self):
        self.run_daily_flow(STARRAIL_DAILY_FLOW)
