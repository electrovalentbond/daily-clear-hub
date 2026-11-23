from games import rewards
from games.zzz import features

# 路线参考绝区零一条龙的邮件应用。以预先打开的菜单为起点，使用实机模板。
DAILY_FLOW = rewards.RewardFlow(
    game_id="zzz",
    home=features.HOME,
    back=features.BACK,
    popup=features.REWARD_POPUP,
    pages=(
        rewards.RewardPage(
            step_id="zzz_claim_mail",
            name="邮件附件领取",
            route=((features.MAIL_ENTRY, features.MAIL_PAGE),),
            claim=features.MAIL_CLAIM,
            empty=features.MAIL_EMPTY,
        ),
    ),
)
