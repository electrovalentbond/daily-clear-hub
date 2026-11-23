from games.pcr import features as F
from games.rewards import RewardFlow, RewardPage


DAILY_FLOW = RewardFlow(
    game_id="pcr",
    home=F.HOME,
    back=F.BACK,
    popup=F.REWARD_CLOSE,
    pages=(
        RewardPage(
            step_id="pcr_collect_gifts",
            name="公主连结礼物领取",
            route=((F.GIFT_ENTRY, F.GIFT_PAGE),),
            claim=F.GIFT_CLAIM,
            empty=F.GIFT_EMPTY,
        ),
        RewardPage(
            step_id="pcr_collect_quests",
            name="公主连结任务领奖",
            route=((F.QUEST_ENTRY, F.QUEST_PAGE),),
            claim=F.QUEST_CLAIM,
            empty=F.QUEST_EMPTY,
        ),
    ),
)
