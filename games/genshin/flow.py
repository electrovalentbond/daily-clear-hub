from games.genshin import features as F
from games.rewards import Key, RewardFlow, RewardPage


DAILY_FLOW = RewardFlow(
    game_id="genshin",
    home=F.HOME,
    back=F.BACK,
    popup=F.REWARD_CLOSE,
    pages=(
        RewardPage(
            step_id="gi_mail",
            name="原神邮件奖励",
            route=((Key("esc"), F.PAIMON_PAGE), (F.MAIL_ENTRY, F.MAIL_PAGE)),
            claim=F.MAIL_CLAIM,
            empty=F.MAIL_EMPTY,
        ),
        RewardPage(
            step_id="gi_commissions",
            name="冒险历练点奖励",
            route=((Key("f1"), F.HANDBOOK_PAGE), (F.COMMISSION_TAB, F.COMMISSION_PAGE)),
            claim=F.ENCOUNTER_CLAIM,
            empty=F.ENCOUNTER_EMPTY,
        ),
        RewardPage(
            step_id="gi_battle_pass",
            name="原神纪行奖励",
            route=(
                (Key("f4"), F.BATTLE_PASS_PAGE),
                (F.BATTLE_PASS_REWARDS_TAB, F.BATTLE_PASS_REWARDS_PAGE),
            ),
            claim=F.BATTLE_PASS_CLAIM,
            empty=F.BATTLE_PASS_EMPTY,
        ),
    ),
)
