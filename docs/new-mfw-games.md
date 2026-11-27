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
3. 先添加「进入大厅」和「每日奖励」。验证后可以添加「前哨基地」「咨询」「模拟室」等任务，或从任务队列应用「快速日常」预设。MDA 上游免费档为每天 10 分钟，可添加「额度显示」查看剩余时间。[快速日常预设](https://github.com/1204244136/MDA/blob/v1.13.10/assets/tasks/preset/QuickDaily.json) · [上游运行额度](https://github.com/1204244136/MDA/blob/v1.13.10/agent/go-service/taskersink/membership/memberdata.go#L182-L284)

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
