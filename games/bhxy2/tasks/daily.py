from games.base import GameTask
from games.bhxy2.flow import BHXY2_DAILY_FLOW, DEFAULT_STEP_TOGGLES, STEP_LABELS
from games.task_config import build_step_config


class Bhxy2DailyTask(GameTask):
    game_id = "bhxy2"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "崩坏学园2 日常"
        self.description = (
            "签到、冒险扫荡、商店免费、邮件等 MVP 日常（ADB）。"
            "社区方案较少，需在雷电模拟器上逐步补模板图。"
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
        self.run_daily_flow(BHXY2_DAILY_FLOW)
