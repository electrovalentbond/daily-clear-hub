"""崩坏 3 模板名称。各入口和状态需要使用当前客户端截图标注。"""

HOME = "bh3_main_menu"  # 舰桥专有图标，避开公告弹窗及返回图标。
BACK = "bh3_back"  # 作战任务、邮箱共用的返回按钮。
REWARD_POPUP = "bh3_reward_popup_close"  # 领奖弹窗专用关闭目标，不能匹配普通确认按钮。

MISSIONS_ENTRY = "bh3_missions_entry"  # 舰桥「任务」入口。
MISSIONS_PAGE = "bh3_missions_page"  # 任务导航栏中稳定可见的元素。
DAILY_ENTRY = "bh3_daily_entry"  # 「作战任务」标签。
DAILY_PAGE = "bh3_daily_page"  # 作战任务页专有的内容标记。
DAILY_CLAIM = "bh3_daily_claim"  # 可点击的「一键领取」按钮，需包括启用样式。
DAILY_EMPTY = "bh3_daily_empty"  # 同一按钮不可领取时的灰色样式。

MAIL_ENTRY = "bh3_mail_entry"  # 舰桥邮件图标。
MAIL_PAGE = "bh3_mail_page"  # 邮件页稳定可见的元素，例如标题。
MAIL_CLAIM = "bh3_mail_claim_all"  # 包含启用样式的「一键领取」按钮。
MAIL_EMPTY = "bh3_mail_empty"  # 邮件页不可领取状态，例如灰色按钮。
