from games import rewards
from games.honkai3 import features

# 路线参考 Maa_bbb。请在当前客户端校准页面标记及领取按钮的两种状态。
DAILY_FLOW = rewards.RewardFlow(
    game_id="honkai3",
    home=features.HOME,
    back=features.BACK,
    popup=features.REWARD_POPUP,
    pages=(
        rewards.RewardPage(
            step_id="bh3_claim_daily",
            name="作战任务一键领取",
            route=(
                (features.MISSIONS_ENTRY, features.MISSIONS_PAGE),
                (features.DAILY_ENTRY, features.DAILY_PAGE),
            ),
            claim=features.DAILY_CLAIM,
            empty=features.DAILY_EMPTY,
        ),
        rewards.RewardPage(
            step_id="bh3_claim_mail",
            name="邮件附件领取",
            route=((features.MAIL_ENTRY, features.MAIL_PAGE),),
            claim=features.MAIL_CLAIM,
            empty=features.MAIL_EMPTY,
        ),
    ),
)
