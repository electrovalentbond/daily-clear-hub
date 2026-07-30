from games.base import GameTask
from games.task_config import build_step_config
from games.zzz.flow import DEFAULT_STEP_TOGGLES, STEP_LABELS, ZZZ_DAILY_FLOW


class ZzzDailyTask(GameTask):
    game_id = "zzz"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "绝区零 日常"
        self.description = (
            "营业刮卡、消耗电量、每日任务、邮件等 MVP 日常。"
            "参考绝区零一条龙流程，Windows 联调时需补充 assets 模板图。"
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
        self.run_daily_flow(ZZZ_DAILY_FLOW)
