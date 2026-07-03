from games.base import GameTask
from games.pcr.flow import (
    DEFAULT_STEP_TOGGLES,
    PCR_DAILY_FLOW,
    STEP_LABELS,
)
from games.task_config import build_step_config


class PcrDailyTask(GameTask):
    game_id = "pcr"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "公主连结 日常"
        self.description = (
            "礼物、任务、扫荡、地下城支援、行会捐赠等农场 MVP 日常。"
            "参考 Princess-connection-farm，分辨率建议 540x960。"
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
        self.run_daily_flow(PCR_DAILY_FLOW)
