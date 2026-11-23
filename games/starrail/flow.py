from games import rewards
from games.starrail import features

# 路线参考三月七小助手的触屏布局。需校准领取按钮的启用和置灰状态。
DAILY_FLOW = rewards.RewardFlow(
    game_id="starrail",
    home=features.HOME,
    back=features.BACK,
    popup=features.REWARD_POPUP,
    pages=(
        rewards.RewardPage(
            step_id="sr_claim_mail",
            name="邮件附件领取",
            route=((features.MAIL_ENTRY, features.MAIL_PAGE),),
            claim=features.MAIL_CLAIM,
            empty=features.MAIL_EMPTY,
        ),
    ),
)
