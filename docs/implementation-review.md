# 七款游戏的日常实现评估

2026 年 11 月 23 日核对上游源码及发布版本。源码链接指向本次检查的提交或发行标签。

Hub 统一了队列入口、日常选择、运行超时和结果判定。七款游戏都可使用上游自带的素材。六款游戏可在 AUTO-MAS 集中设置，公主连结 B 服可从同一个 Hub 命令发现并运行。实际任务范围由区服、登录与托管设置决定。内置 ok-script 路线依然适用于使用本机模板的免费领奖。

## MAA 与 MaaFramework

明日方舟 MAA 将日常奖励、邮件等拆为各自可启停的子任务。刷图另外负责关卡导航、理智资源保护、次数和结算。MaaFramework 的 Pipeline 先匹配当前界面，再执行动作并检查后继节点，超时或动作失败可以进入错误处理。Hub 沿用状态检查的做法，由 ok-script 采集画面和发送输入。[MAA 领奖](https://github.com/MaaAssistantArknights/MaaAssistantArknights/blob/40472436115fc9906269f72bfc737bc227737b22/src/MaaCore/Task/Interface/AwardTask.cpp#L10-L60) · [MAA 刷图](https://github.com/MaaAssistantArknights/MaaAssistantArknights/blob/40472436115fc9906269f72bfc737bc227737b22/src/MaaCore/Task/Interface/FightTask.cpp#L17-L102) · [MaaFramework Pipeline](https://github.com/MaaXYZ/MaaFramework/blob/86853d162fe581611432f63087b0a432898bb95b/docs/en_us/3.1-PipelineProtocol.md#L23-L72)

旧流程常在点到某个按钮后直接报告完成，找不到按钮时也可能计为跳过。现在先确认主界面和每层目的页，再识别可领按钮、领取反馈和页面领空状态。确认无奖励与识别失败分别报告。每项尝试回到对应主界面，点击次数有上限。外部工具接入也需要可信的运行结果，不能只把进程启动或窗口关闭计为完成。

## 各游戏

### 崩坏 3

旧流程用通用按钮串起材料远征、家园和舰团。Maa_bbb 将它们作为独立流程，还有专门的作战任务及邮件领奖操作。Hub 内置舰桥进入作战任务领奖和邮件附件领取。Maa_bbb 可作为通用 MFW 项目由 AUTO-MAS 执行。Hub 核对项目来源，取得本轮任务 ID 后读取账号完成报告。[Maa_bbb 功能与启动参数](https://github.com/miaojiuqing/Maa_bbb/blob/fab1d55b73ab8a6016be0888a18f5928463e2b83/README.md#主要功能) · [奖励节点](https://github.com/miaojiuqing/Maa_bbb/tree/fab1d55b73ab8a6016be0888a18f5928463e2b83/assets/resource/base/pipeline/日常/奖励领取) · [启动器完成动作](https://github.com/overflow65537/MFW-PyQt6/blob/4ce4fe72ec54424f6aa97a696b8cb721bd365d59/app/core/runner/task_flow.py#L4444-L4454)

### 崩坏：星穹铁道

旧开拓力流程缺少关卡选择、战斗结束和领取消耗检查。内置步骤只领取邮件，起点是已打开的手机菜单，按实际布局校准。可在 AUTO-MAS 的 HSR 托管中复用三月七小助手配置。独立三月七后端仍可运行 `routine`，按其配置安排清开拓力、委托、实训与领奖，并提供命令行退出码。它会比 `daily` 多执行日常准备阶段，后者仍可按配置先领奖再做实训。[手机菜单和邮件](https://github.com/moesnow/March7thAssistant/blob/311fa27974216a0d2824d111a3ad81845af7e297/assets/touch_720/screens.json#L36-L58) · [日常编排](https://github.com/moesnow/March7thAssistant/blob/311fa27974216a0d2824d111a3ad81845af7e297/tasks/daily/daily.py#L47-L87) · [退出码](https://github.com/moesnow/March7thAssistant/blob/311fa27974216a0d2824d111a3ad81845af7e297/main.py#L24-L33)

### 绝区零

旧流程把刮卡、电量和任务奖励简化成少数入口按钮。绝区零一条龙的刮卡需要到店交互，电量消耗依赖关卡和结算，活跃度奖励有独立条件。Hub 内置从已打开的游戏菜单领取邮件附件。AUTO-MAS 绝区零专项利用本轮日志和应用记录判定配置中的各项任务。Hub 以该轮的账号结果判定完成情况。[邮件流程](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon/blob/734e1321706d4802bb851e77d09d9393fb1c2889/src/zzz_od/application/email_app/email_app.py#L33-L82) · [活跃度判断](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon/blob/734e1321706d4802bb851e77d09d9393fb1c2889/src/zzz_od/application/engagement_reward/engagement_reward_app.py#L35-L85) · [AUTO-MAS 终态判定](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/ZzzOd/AutoProxy.py#L1169-L1247)

### 原神

BetterGI 从冒险之证领历练点，再去冒险家协会领委托和派遣奖励。秘境需要导航、战斗和石化古树领奖。旧流程里的通用「树脂本扫荡」无法表达这些状态。内置流程保留邮件、冒险历练点和可选的纪行奖励页，采用游戏默认的 Esc、F1、F4 导航。协会领取和重新派遣需要额外导航，移出内置范围。AUTO-MAS 原神专项运行配置里指定的一条龙。上游把分步执行失败标记为部分失败，Hub 在本轮账号报告中将其计入未完成。少数领取操作仍以 BetterGI 本身的核验能力为限。[历练点流程](https://github.com/babalae/better-genshin-impact/blob/5a88c99ba16cd9808c447cda128adb8fe488c288/BetterGenshinImpact/GameTask/Common/Job/ClaimEncounterPointsRewardsTask.cs#L67-L149) · [日常奖励](https://github.com/babalae/better-genshin-impact/blob/5a88c99ba16cd9808c447cda128adb8fe488c288/BetterGenshinImpact/GameTask/Common/Job/ClaimDailyRewardsTask.cs#L45-L71) · [秘境战斗](https://github.com/babalae/better-genshin-impact/blob/5a88c99ba16cd9808c447cda128adb8fe488c288/BetterGenshinImpact/GameTask/AutoDomain/AutoDomainTask.cs#L435-L507) · [AUTO-MAS 日常结果](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/BetterGI/AutoProxy.py#L2177-L2205)

### 公主连结

Princess-connection-farm 用不同的页面和按钮状态识别礼物与任务奖励，也处理礼物上限。Rino 的主线扫荡有预设、次数、体力判断等分支。旧流程只尝试通用冒险入口和扫荡按钮，地下城支援及行会捐赠也未确认实际结果。Hub 内置礼物和任务奖励。公主连结国服 B 服可改用 pcr-script，它提供自带素材、日程表、任务与礼物领奖，并输出带核验字段的 JSON。日程表和其他消费项目按游戏与上游配置执行。[旧农场实现](https://github.com/SimonShi1994/Princess-connection-farm/blob/dc37848d2437ce66e92d9e82186beae13d679c08/automator_mixins/_routine.py#L235-L266) · [Rino 主线扫荡](https://github.com/miaoyu2233/Rino_PCRautomation/blob/4e3a3fc9bf7f1132804bd807bd467b484d841551/Resource/base/pipeline/masterstroke_Sweep_task.json#L33-L107) · [pcr-script 结果协议](https://github.com/Gibberer/pcr-script/blob/d1eb2120599a5bc42ce934657f7788e1a8f0bfc3/pcrscript/runtime.py#L167-L211)

### 崩坏学园 2

旧流程会在商店匹配通用「购买」，冒险也可能点击「挑战」。HKA 按价格为零、剩余免费次数和结算变化处理这类日常。Hub 内置从「社交 → 我的消息」收邮件和从「任务 → 存在感」领奖。新增 MaaBH2，可把每日与每周领奖、社团等任务集中到 AUTO-MAS。[MaaBH2 上游配置](maabh2.md)

可选 HKA 后端按用户配置执行商店、免费快捷战斗、体力本、探险和领奖等工作，等待进程并核对最后的 JSON 运行报告。退出码为零时仍要确认报告，因为取消也可返回零。[HKA 免费检查](https://github.com/lolineet/Honkai2Automation/blob/08052330d5294b53b5578416fbbd97c8aca3b180/hka/game_flows.py#L553-L622) · [快捷战斗](https://github.com/lolineet/Honkai2Automation/blob/08052330d5294b53b5578416fbbd97c8aca3b180/hka/game_flows.py#L695-L798) · [命令行结果](https://github.com/lolineet/Honkai2Automation/blob/08052330d5294b53b5578416fbbd97c8aca3b180/hka/cli.py#L64-L94) · [最终运行报告](https://github.com/lolineet/Honkai2Automation/blob/08052330d5294b53b5578416fbbd97c8aca3b180/hka/runner.py#L188-L216)

### 明日方舟：终末地

MaaEnd 将日常奖励拆成邮件、暂存区、活跃、通行证、活动等分支。原仓库已经要求确认页面和领空状态，但把各项都当作菜单直达。Hub 从邮箱进入暂存区，从行动手册进入日常活跃页，从通行证进入奖励页，并保留四号谷地模拟空间和简制手册当前条目的可选领奖。协议空间与基建可在 MaaEnd 的独立 MFW 托管中选配。Hub 核对 MaaEnd 项目来源，读取 AUTO-MAS 的运行 ID 和最终账号完成报告。[日常分支](https://github.com/MaaEnd/MaaEnd/blob/7179ee06b2aa05d6087821279d43810a7f9c4433/assets/resource/pipeline/DailyRewards.json#L2-L90) · [邮件与暂存区](https://github.com/MaaEnd/MaaEnd/blob/7179ee06b2aa05d6087821279d43810a7f9c4433/assets/resource/pipeline/DailyRewards/Emails.json#L192-L374) · [行动手册导航](https://github.com/MaaEnd/MaaEnd/blob/7179ee06b2aa05d6087821279d43810a7f9c4433/assets/resource/pipeline/Interface/SceneMenu.json#L165-L185) · [AUTO-MAS 任务接口](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/docs/testing/e2e.md#后端公开契约)

## 验证范围

上游后端需要独立安装和首次配置，可直接使用上游提供的素材。内置路线需要采集本机模板。自动化测试覆盖托管身份校验、终态结果处理与队列调度。Windows 上的截图、点击及奖励到账仍需实机验证。[Windows 命令手册](windows.md) · [模板素材说明](../assets/README.md)
