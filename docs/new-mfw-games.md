# NIKKE 国际服、学园偶像大师和 Dot Abyss

## 下载和添加托管

在 Windows 的 `daily-clear-hub` 仓库根目录运行。已有的 AUTO-MAS 会继续使用原安装路径。安装时用过 `-ToolsRoot` 的话，传入同一个目录。

```powershell
git pull --ff-only
& .\scripts\setup-windows.ps1 -Games nikke,gakumas,dotabyss
```

可以只传入需要的游戏 ID。完成后到 **AUTO-MAS → 托管管理 → 新建托管 → MFW 脚本**，逐个导入下面指定的目录。等「运行环境」准备好，再为每个托管添加并启用账号，在账号的「任务队列」里添加日常。单个托管验证成功后，从现有「调度队列」点「添加任务」把它加入原来的队列。[AUTO-MAS MFW 配置指南](https://doc.auto-mas.top/docs/script-guide/maafw.html)

## NIKKE 国际服

1. 导入 `nikke:` 后面的 MDA 目录，资源选「国际服」。进游戏登录，把**游戏内语言**设为「简体中文」。MDA 自己的界面可以显示英文，游戏识别用的是简中画面。[MDA 语言适配](https://github.com/1204244136/MDA/blob/v1.13.10/README.md#语言适配说明) · [Windows 发布包](https://github.com/1204244136/MDA/releases/tag/v1.13.10)
2. **Windows 客户端**先用官方启动器打开游戏。在 MFW 控制器选「电脑端-默认」，「PC 游戏启动方式」选「由脚本自身控制游戏」，运行时让 AUTO-MAS 接管已打开的窗口。第一次连接前可让窗口处于可见状态。**安卓模拟器**选「安卓端」，绑定安装了国际服且已登录的实例。「游戏包名」填 `com.proximabeta.nikke`，AUTO-MAS 可随模拟器启动游戏。[控制器设置](https://github.com/1204244136/MDA/blob/v1.13.10/assets/interface.json) · [国际服安卓包名](https://play.google.com/store/apps/details?id=com.proximabeta.nikke)
3. 先添加「进入大厅」和「每日奖励」。验证后可以添加「前哨基地」「咨询」「模拟室」等任务，或从任务队列应用「快速日常」预设。MDA 免费档每天有 **10 分钟的 MDA 自动化运行时间**，北京时间 04:00 刷新，收费档可增加额度。用「额度显示」查看剩余时间。UU 加速时长由你的 UU 账户套餐决定。[快速日常预设](https://github.com/1204244136/MDA/blob/v1.13.10/assets/tasks/preset/QuickDaily.json) · [MDA 额度源码](https://github.com/1204244136/MDA/blob/v1.13.10/agent/go-service/taskersink/membership/quota.go) · [MDA 会员方案](https://doropay.top/)

**也可以独立使用 NKAS。** NIKKEAutoScript 支持国际服 Windows 和 ADB，其 PC 指南要求简中，ADB 的英文识别覆盖部分任务。NKAS 自带常驻调度。需要在同一个 AUTO-MAS 队列中逐项选任务时，使用上面的 MDA 托管。[NKAS 发布页](https://github.com/megumiss/NIKKEAutoScript/releases/tag/v1.2.0) · [Windows 配置](https://github.com/megumiss/NIKKEAutoScript/wiki/Quick-Installation-Guide.zh-CN) · [模拟器配置](https://github.com/megumiss/NIKKEAutoScript/wiki/Usage-Guide-Emulator.zh-CN)

## 学园偶像大师

1. 导入 `gakumas:` 后面的 MaaGakumasu 目录。[Windows 发布包](https://github.com/SuperWaterGod/MaaGakumasu/releases/tag/v1.5.4)
2. **安卓日服**选「模拟器」和「官服」，使用插件汉化时改选「插件版汉化」。绑定已登录的实例，游戏包名填 `com.bandainamcoent.idolmaster_gakuen`。上游主要在 MuMu 12 测试，推荐 `1280×720`、`240 DPI`。将「启动游戏」放在队列前面，处理登录后的弹窗。[适配说明](https://github.com/SuperWaterGod/MaaGakumasu/blob/v1.5.4/README.md#L74-L89) · [安卓启动节点](https://github.com/SuperWaterGod/MaaGakumasu/blob/v1.5.4/assets/resource/base/pipeline/StartUp.json#L15-L50)
3. **DMM 日服**选「PC」和「DMM」。以管理员权限打开 AUTO-MAS，从 DMM 官方启动器打开游戏并进入主页。「PC 游戏启动方式」选「由脚本自身控制游戏」，运行前保持游戏窗口打开。插件汉化的 DMM 资源也可选择，上游测试覆盖有限。[DMM 启动节点](https://github.com/SuperWaterGod/MaaGakumasu/blob/v1.5.4/assets/resource/DMM/pipeline/StartUp.json)
4. 日常可以先加「收取活动费」「领取奖励」，再按需加「安排工作」「社团活动」「每日挑战」和「每周免费初星包」。使用上游「一键日常」预设时，留意其中的好友扭蛋和金币兑换选项。[一键日常预设](https://github.com/SuperWaterGod/MaaGakumasu/blob/v1.5.4/assets/tasks/preset.json#L1-L76)

## Dot Abyss

当前接入面向 Windows 上的 **日文 DMM 客户端「ドットアビスX」**。按上游要求，通过 DMM Game Player 手动打开游戏，进入主界面并将游戏窗口设为 `1280×720`。识别使用游戏窗口截图和支持图像输入的 OpenAI 兼容模型。云端模型会接收截图，费用按所选供应商计。[MaaDotAbyss 使用说明](https://github.com/Azure-Sora/MaaDotAbyss/blob/v0.2.0/README.md)

1. 从安装脚本输出复制 `dotabyss project:` 和 `dotabyss Python:` 对应的完整路径，替换以下两个占位符。通过上游界面「模型」页设置 API 地址、密钥和支持图像输入的模型。保存并选为默认后退出，日常运行会读取同一份本机配置。

   ```powershell
   Push-Location '<dotabyss project 的实际路径>'
   try { & '<dotabyss Python 的实际路径>' .\run_gui.py }
   finally { Pop-Location }
   ```

2. 导入 `dotabyss AUTO-MAS project:` 对应的适配器目录。控制器选「DMM 游戏窗口」，资源选「日文 DMM 客户端」。「PC 游戏启动方式」选「由脚本自身控制游戏」，运行前打开游戏并保持窗口可见。在「基本信息」打开「跟随来源目录」，之后更新 Hub 或重跑安装脚本时可以点「立即同步」。
3. 先单独运行「领取礼物」或「领取任务奖励」，也可以应用「基础领奖」预设。势力任务、迎击战和探索队任务依赖于模型识别当前画面，先分别验证再放进定时队列。「领取挂机奖励」可能确认装备自动分解，按游戏中已有的分解设置执行。[上游日常任务定义](https://github.com/Azure-Sora/MaaDotAbyss/blob/v0.2.0/tasks/daily.yaml)

## 可选的 UU 加速

在 Windows 安装并登录**网易 UU 客户端**。先在 UU 为每款游戏手动成功加速一次，记下搜索结果中的完整卡片名称。按你用的客户端选 UU 条目，例如 NIKKE 国际服电脑端、模拟器或日服 DMM。Dot Abyss 请在你自己的 UU 游戏库里确认有对应的 DMM 条目并能正常加速。[UU 加速和游戏启动说明](https://uu.baike.netease.com/zhinan/53.html)

在 Hub 仓库根目录运行，也可以只列需要 UU 的游戏。自定义过 `-ToolsRoot` 时沿用原值。

```powershell
git pull --ff-only
& .\scripts\setup-windows.ps1 -Games nikke,gakumas,dotabyss -WithUu
```

1. 在 AUTO-MAS 新建「MFW 脚本」，导入每款游戏输出中 `UU AUTO-MAS project:` 后面的目录。按上文选择控制器和资源、添加账号，再把这份托管放进现有队列。如果这款游戏已有普通托管，从队列里把该项换成含 UU 的托管即可。
2. 打开该账号的「任务队列」。先添加需要的日常或应用预设，再点「添加任务」，搜索并勾选「切换网易 UU 加速」。填写 UU 中的游戏全名。要强制核对区服时，填写 UU 显示的区服文字。UU 已打开时可留空程序路径；需要由脚本打开，且默认安装位置未找到时，再填 `uu.exe` 或 `uu_launcher.exe` 的完整路径。若还有别的启动前任务，把 UU 放在最前面。[AUTO-MAS 前置任务的执行顺序](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/MaaFW/tools/embedded/runner_task.py#L873-L889)
3. 解锁桌面并试跑该托管。脚本会打开或接管 UU，必要时停止旧加速，确认目标游戏显示加速状态后再继续。无法确认时，本次运行在前置任务处失败，可到历史记录查看原因。DMM 仍按上文通过官方启动器进入游戏，前置任务执行时保持 UU 窗口可见。

取消勾选「切换网易 UU 加速」即可跳过这一步。含 UU 的托管用本地项目，更新时重跑包含 `-WithUu` 的安装命令，然后在托管「基本信息」开启「跟随来源目录」并点「立即同步」。
