from games.base import GameTask
from games.honkai3.flow import (
    DEFAULT_STEP_TOGGLES,
    HONKAI3_DAILY_FLOW,
    STEP_LABELS,
)
from games.task_config import build_step_config


class Honkai3DailyTask(GameTask):
    game_id = "honkai3"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "崩坏3 日常"
        self.description = (
            "材料远征、家园、舰团、领奖等 MVP 日常。"
            "参考 Maa_bbb 任务拆分，Windows 联调时需补充 assets 模板图。"
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
        self.run_daily_flow(HONKAI3_DAILY_FLOW)
