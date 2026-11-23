from games.bhxy2 import features as F
from games.rewards import RewardFlow, RewardPage


DAILY_FLOW = RewardFlow(
    game_id="bhxy2",
    home=F.HOME,
    back=F.BACK,
    popup=F.REWARD_CLOSE,
    pages=(
        RewardPage(
            step_id="bh2_mail",
            name="崩坏学园2 邮件奖励",
            route=((F.SOCIAL_ENTRY, F.SOCIAL_PAGE), (F.MAIL_ENTRY, F.MAIL_PAGE)),
            claim=F.MAIL_CLAIM,
            empty=F.MAIL_EMPTY,
        ),
        RewardPage(
            step_id="bh2_presence",
            name="存在感奖励",
            route=((F.TASK_ENTRY, F.TASK_PAGE), (F.PRESENCE_TAB, F.PRESENCE_PAGE)),
            claim=F.PRESENCE_CLAIM,
            empty=F.PRESENCE_EMPTY,
        ),
    ),
)
