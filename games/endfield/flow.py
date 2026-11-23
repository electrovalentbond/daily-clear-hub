from games.endfield import features as F
from games.rewards import Key, RewardFlow, RewardPage


MENU = (Key("esc"), F.MENU_PAGE)
MAIL = (Key("k"), F.MAIL_PAGE)
OPERATIONAL_MANUAL = (F.OPERATIONAL_MANUAL_ENTRY, F.OPERATIONAL_MANUAL_PAGE)

DAILY_FLOW = RewardFlow(
    game_id="endfield",
    home=F.HOME,
    back=F.BACK,
    popup=F.REWARD_CLOSE,
    pages=(
        RewardPage(
            step_id="ef_mail",
            name="终末地邮件奖励",
            route=(MAIL,),
            claim=F.MAIL_CLAIM,
            empty=F.MAIL_EMPTY,
        ),
        RewardPage(
            step_id="ef_storage",
            name="暂存区领取",
            route=(MAIL, (F.STORAGE_ENTRY, F.STORAGE_PAGE)),
            claim=F.STORAGE_CLAIM,
            empty=F.STORAGE_EMPTY,
        ),
        RewardPage(
            step_id="ef_simulation",
            name="四号谷地模拟空间奖励",
            route=(
                MENU,
                OPERATIONAL_MANUAL,
                (F.SIMULATION_TAB, F.SIMULATION_TAB_PAGE),
                (F.SIMULATION_VALLEY_ENTRY, F.SIMULATION_PAGE),
            ),
            claim=F.SIMULATION_CLAIM,
            empty=F.SIMULATION_EMPTY,
        ),
        RewardPage(
            step_id="ef_handbook",
            name="简制手册当前条目奖励",
            route=(
                (Key("b"), F.BACKPACK_PAGE),
                (F.CRAFTING_ENTRY, F.CRAFTING_PAGE),
                (F.HANDBOOK_ENTRY, F.HANDBOOK_PAGE),
                (F.HANDBOOK_ITEM_ENTRY, F.HANDBOOK_ITEM_PAGE),
            ),
            claim=F.HANDBOOK_CLAIM,
            empty=F.HANDBOOK_EMPTY,
        ),
        RewardPage(
            step_id="ef_daily",
            name="终末地日常活跃奖励",
            route=(MENU, OPERATIONAL_MANUAL, (F.DAILY_TAB, F.DAILY_PAGE)),
            claim=F.DAILY_CLAIM,
            empty=F.DAILY_EMPTY,
        ),
        RewardPage(
            step_id="ef_pass",
            name="终末地通行证奖励",
            route=(
                MENU,
                (F.PASS_ENTRY, F.PASS_PAGE),
                (F.PASS_REWARDS_TAB, F.PASS_REWARDS_PAGE),
            ),
            claim=F.PASS_CLAIM,
            empty=F.PASS_EMPTY,
        ),
    ),
)
