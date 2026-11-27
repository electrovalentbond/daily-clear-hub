# NIKKE 国际服、学园偶像大师和 Dot Abyss

## 下载和添加托管

在 Windows 的 `daily-clear-hub` 仓库根目录运行。已有的 AUTO-MAS 会继续使用原安装路径。安装时用过 `-ToolsRoot` 的话，传入同一个目录。

```powershell
git pull --ff-only
& .\scripts\setup-windows.ps1 -Games nikke,gakumas,dotabyss
```

可以只传入需要的游戏 ID。NIKKE 的 NKAS 托管由安装脚本自动注册。学园偶像大师和 Dot Abyss 在 **AUTO-MAS → 托管管理 → 新建托管 → MFW 脚本** 导入。等「运行环境」准备好，再添加账号和任务。单个托管验证成功后，从现有「调度队列」点「添加任务」加入队列。[AUTO-MAS MFW 配置指南](https://doc.auto-mas.top/docs/script-guide/maafw.html)

## NIKKE 国际服

NIKKE 国际服使用开源 [NIKKEAutoScript（NKAS）](https://github.com/megumiss/NIKKEAutoScript) 的 Windows 完整包。AUTO-MAS 触发一轮运行，NKAS 根据自己的实例配置执行已启用且到期的任务，随后退出，把控制交还队列。已经完成或尚未到运行时间的项目会按 NKAS 的日程跳过。[NKAS v1.2.0 发布包](https://github.com/megumiss/NIKKEAutoScript/releases/tag/v1.2.0)

1. 在仓库目录运行以下命令。它会安装 NKAS，启动或连接 AUTO-MAS，并自动注册 **NIKKE 国际服（NKAS）** 和默认账号。AUTO-MAS 首次初始化需要等待。NKAS 安装目录须使用 ASCII 字符，必要时用 `-ToolsRoot 'C:\Tools\DailyAutomation'`；如果 AUTO-MAS 使用自定义本机端口，传 `-AutoMasPort`。需要 UU 时，安装命令加 `-WithUu`。[Windows 自带 tar.exe 支持的格式](https://learn.microsoft.com/en-us/windows/tar/)

   ```powershell
   git pull --ff-only
   & .\scripts\setup-windows.ps1 -Games nikke
   ```

2. 在 **AUTO-MAS → 托管管理 → NIKKE 国际服（NKAS）→ NKAS 本机实例**，点账号页右上角的 **「通用配置」**。它会打开 NKAS 的本机网页。首次创建名为 `nkas` 的实例，选「国际服」并连接客户端。在 NKAS 的「调度设置」逐项启用所需的邮件、前哨收益、派遣和任务领奖等项目，点网页的「保存」，再回 AUTO-MAS 点「保存配置」结束会话。日常由 AUTO-MAS 调度，NKAS 配置页无需手动启动任务。该实例的 NKAS「串行模式」需关闭。[NKAS 配置指南](https://github.com/megumiss/NIKKEAutoScript/wiki/Configuration-Guide)

   - **Windows 客户端**使用简体中文的游戏界面，按 NKAS 指南指定官方启动器并先登录一次。以管理员权限运行 AUTO-MAS。NKAS 根据保存的启动器配置打开游戏。[Windows 配置指南](https://github.com/megumiss/NIKKEAutoScript/wiki/Quick-Installation-Guide.zh-CN)
   - **安卓模拟器**先启动已登录的模拟器实例，在 NKAS 里填写其实际 ADB 序列号，资源选「国际服」。简体中文覆盖较完整，ADB 英文仅覆盖部分任务。运行前保留模拟器在线。[模拟器配置指南](https://github.com/megumiss/NIKKEAutoScript/wiki/Usage-Guide-Emulator.zh-CN)

3. 在 AUTO-MAS「调度队列 → 添加任务」加入 **NIKKE 国际服（NKAS）**。之后从同一个「通用配置」入口修改 NKAS 的任务开关。单轮结果在 AUTO-MAS 历史记录查看，识别、登录和设备细节在 NKAS 项目的 `log` 目录。若首次安装等待 AUTO-MAS 初始化超时，等应用打开后重跑同一条安装命令。[AUTO-MAS 通用托管](https://doc.auto-mas.top/docs/script-guide/general.html)

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

### NIKKE 国际服

安装时加 `-WithUu`，脚本会启用 NKAS 托管的加速选项。在输出的 `nikke adapter settings:` 对应 `nikke.json` 中填写 `uu.game` 为卡片全名。需要核对区服可填 `uu.region`。UU 未打开且安装目录无法自动查找时，再填 `uu.exe` 字段为 `uu.exe` 或 `uu_launcher.exe` 的完整路径。UU 确认加速成功后，托管才会运行 NKAS。想关掉时，在托管的「脚本参数」删除 `|` 前面的 `--uu`。

### 学园偶像大师和 Dot Abyss

1. 在 AUTO-MAS 新建「MFW 脚本」，导入输出中 `UU AUTO-MAS project:` 后面的目录。按上文选择控制器和资源、添加账号，再把这份托管放进现有队列。如果这款游戏已有普通托管，从队列里把该项换成含 UU 的托管即可。
2. 打开该账号的「任务队列」。先添加需要的日常或应用预设，再点「添加任务」，搜索并勾选「切换网易 UU 加速」。填写 UU 中的游戏全名。要强制核对区服时，填写 UU 显示的区服文字。UU 已打开时可留空程序路径；需要由脚本打开，且默认安装位置未找到时，再填 `uu.exe` 或 `uu_launcher.exe` 的完整路径。若还有别的启动前任务，把 UU 放在最前面。[AUTO-MAS 前置任务的执行顺序](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/MaaFW/tools/embedded/runner_task.py#L873-L889)
3. 解锁桌面并试跑该托管。脚本会打开或接管 UU，必要时停止旧加速，确认目标游戏显示加速状态后再继续。无法确认时，本次运行在前置任务处失败，可到历史记录查看原因。DMM 仍按上文通过官方启动器进入游戏，前置任务执行时保持 UU 窗口可见。

取消勾选「切换网易 UU 加速」即可跳过这一步。含 UU 的托管用本地项目，更新时重跑包含 `-WithUu` 的安装命令，然后在托管「基本信息」开启「跟随来源目录」并点「立即同步」。
