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

   - **Windows 客户端**在 NKAS 选「Windows (PC端) → PC 端设置 → 游戏客户端 → 国际」，选择检测到的安装，或填写官方 `Launcher\nikke_launcher.exe` 的完整路径和游戏路径。先手动登录一次，使用简体中文界面，以管理员权限运行 AUTO-MAS。保持 AUTO-MAS 通用托管里的游戏启动开关关闭。NKAS 会在有需要运行的任务时自行打开启动器并点启动，启用 UU 时会先加速。Google 登录失效或出现验证码时，在官方启动器恢复登录后重试。[NKAS Windows 配置](https://github.com/megumiss/NIKKEAutoScript/wiki/Quick-Installation-Guide.zh-CN) · [NKAS 启动实现](https://github.com/megumiss/NIKKEAutoScript/blob/v1.2.0/module/device/win/app_control.py#L199-L259)
   - **安卓模拟器**先启动已登录的模拟器实例，在 NKAS 里填写其实际 ADB 序列号，资源选「国际服」。简体中文覆盖较完整，ADB 英文仅覆盖部分任务。运行前保留模拟器在线。[模拟器配置指南](https://github.com/megumiss/NIKKEAutoScript/wiki/Usage-Guide-Emulator.zh-CN)

3. 在 AUTO-MAS「调度队列 → 添加任务」加入 **NIKKE 国际服（NKAS）**。之后从同一个「通用配置」入口修改 NKAS 的任务开关。单轮结果在 AUTO-MAS 历史记录查看，识别、登录和设备细节在 NKAS 项目的 `log` 目录。若首次安装等待 AUTO-MAS 初始化超时，等应用打开后重跑同一条安装命令。[AUTO-MAS 通用托管](https://doc.auto-mas.top/docs/script-guide/general.html)

若 UU 已加速但 NKAS 报 `Launcher path must be specified`，进入该账号的「通用配置 → nkas → PC 客户端」，在「启动器路径」选中实际安装的 `nikke_launcher.exe`，然后保存。已选择「国际」时仍需指定启动器路径。AUTO-MAS 的失败摘要会显示启动检查的结果。适配器的 `nikke-automas\logs` 下，`run-*.log` 是运行记录，同一时间的 `child-*.log` 是 NKAS 子进程输出。用 Windows PowerShell 读取日志时带上 `-Encoding UTF8`。[NKAS 路径配置](https://github.com/megumiss/NIKKEAutoScript/wiki/Quick-Installation-Guide.zh-CN#4-选择游戏路径)

## 学园偶像大师

1. 导入 `gakumas:` 后面的 MaaGakumasu 目录。[Windows 发布包](https://github.com/SuperWaterGod/MaaGakumasu/releases/tag/v1.5.4)
2. **安卓日服**选「模拟器」和「官服」，使用插件汉化时改选「插件版汉化」。绑定已登录的实例，游戏包名填 `com.bandainamcoent.idolmaster_gakuen`。上游主要在 MuMu 12 测试，推荐 `1280×720`、`240 DPI`。将「启动游戏」放在队列前面，处理登录后的弹窗。[适配说明](https://github.com/SuperWaterGod/MaaGakumasu/blob/v1.5.4/README.md#L74-L89) · [安卓启动节点](https://github.com/SuperWaterGod/MaaGakumasu/blob/v1.5.4/assets/resource/base/pipeline/StartUp.json#L15-L50)
3. **DMM 日服**选「PC」和「DMM」，以管理员权限打开 AUTO-MAS。「PC 游戏启动方式」选「由脚本自身控制游戏」，新版也可能显示「使用其他方式启停游戏」。配置 DMM 快捷方式或 UU 加速后启动。把 MaaGakumasu 自带的「启动游戏」放在普通任务的第一项，进入主页并处理登录后的弹窗。使用插件汉化时选「DMM插件汉化版」。[快捷方式配置](#从-auto-mas-启动-dmm-游戏) · [UU 启动配置](#学园偶像大师和-dot-abyss) · [进入主页流程](https://github.com/SuperWaterGod/MaaGakumasu/blob/v1.5.4/assets/resource/base/pipeline/StartUp.json)
4. 日常可以先加「收取活动费」「领取奖励」，再按需加「安排工作」「社团活动」「每日挑战」和「每周免费初星包」。使用上游「一键日常」预设时，留意其中的好友扭蛋和金币兑换选项。[一键日常预设](https://github.com/SuperWaterGod/MaaGakumasu/blob/v1.5.4/assets/tasks/preset.json#L1-L76)

## Dot Abyss

当前接入面向 Windows 上的 **日文 DMM 客户端「ドットアビスX」**。首次从 DMM GAMES PLAYER 登录游戏并完成引导，将游戏窗口设为 `1280×720`。识别使用游戏窗口截图和支持图像输入的 OpenAI 兼容模型。云端模型会接收截图，费用按所选供应商计。[MaaDotAbyss 使用说明](https://github.com/Azure-Sora/MaaDotAbyss/blob/v0.2.0/README.md)

1. 从安装脚本输出复制 `dotabyss project:` 和 `dotabyss Python:` 对应的完整路径，替换以下两个占位符。通过上游界面「模型」页设置 API 地址、密钥和支持图像输入的模型。点「保存」和「设为主力」后退出，日常运行会读取同一份本机配置。

   ```powershell
   Push-Location '<dotabyss project 的实际路径>'
   try { & '<dotabyss Python 的实际路径>' .\run_gui.py }
   finally { Pop-Location }
   ```

2. 导入 `dotabyss AUTO-MAS project:` 对应的适配器目录。控制器选「DMM 游戏窗口」，资源选「日文 DMM 客户端」。「PC 游戏启动方式」选「由脚本自身控制游戏」，并配置 DMM 快捷方式或 UU 加速后启动。在「基本信息」打开「跟随来源目录」，更新 Hub 并重跑安装脚本后点「立即同步」。[快捷方式配置](#从-auto-mas-启动-dmm-游戏) · [UU 启动配置](#学园偶像大师和-dot-abyss)
3. 先单独运行「领取礼物」或「领取任务奖励」，也可以应用「基础领奖」预设。势力任务、迎击战和探索队任务依赖于模型识别当前画面，先分别验证再放进定时队列。「领取挂机奖励」可能确认装备自动分解，按游戏中已有的分解设置执行。[上游日常任务定义](https://github.com/Azure-Sora/MaaDotAbyss/blob/v0.2.0/tasks/daily.yaml)

## 从 AUTO-MAS 启动 DMM 游戏

以下步骤使用 DMM 官方快捷方式。加速和启动也可以交给同一个 UU 前置任务。[UU 启动配置](#学园偶像大师和-dot-abyss)

1. 登录 DMM GAMES PLAYER，在「マイゲーム」找到对应的已安装游戏，点卡片的 **「︙ → ショートカット作成」**。用生成的桌面快捷方式试开一次，确认能打开游戏本体。只打开游戏详情页时，在 DMM 更新并重新创建快捷方式。[DMM 快捷方式说明](https://support.dmm.com/dlsoft/article/47380) · [旧快捷方式的处理](https://support.dmm.com/games/article/48363)
2. 已有托管在 Windows 的仓库目录运行以下命令。已使用 UU 的托管给安装命令加上 `-WithUu`。有自定义 `-ToolsRoot` 时沿用原值。

   ```powershell
   git pull --ff-only
   & .\scripts\setup-windows.ps1 -Games gakumas,dotabyss
   ```

3. 在当前托管的「基本信息」开启「跟随来源目录」，点「立即同步」。进入账号的「任务队列 → 添加任务」，添加并勾选 **「启动 DMM 游戏」**。AUTO-MAS 会尝试在桌面找到游戏的官方快捷方式，可以先留空「DMM 游戏快捷方式完整路径」。如果找不到或桌面有多个副本，填写该快捷方式的完整 `.lnk` 或 `.url` 路径。
4. 如果同时使用 UU 加速和 DMM 快捷方式，保持「UU 加速后启动 DMM 游戏」关闭，在前置任务区按 **「切换网易 UU 加速」→「启动 DMM 游戏」** 排序。学园偶像大师的普通任务先执行「启动游戏」。配置好后，可关掉游戏本体再试跑一次。AUTO-MAS 会等待对应游戏窗口出现，已打开的游戏窗口可直接复用。保持桌面解锁。DMM 重新登录、需要确认的更新、首次引导等提示应在官方客户端处理后重试。[AUTO-MAS 前置任务执行顺序](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/MaaFW/tools/embedded/runner_task.py#L873-L889)

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

仅安装或更新这两款游戏的含 UU 托管时，在 Windows 的仓库目录运行以下命令。自定义过 `-ToolsRoot` 时沿用原值。

```powershell
git pull --ff-only
& .\scripts\setup-windows.ps1 -Games gakumas,dotabyss -WithUu
```

1. 已有含 UU 托管时，在「基本信息」开启「跟随来源目录」，点「立即同步」。首次配置时，新建「MFW 脚本」并导入输出中 `UU AUTO-MAS project:` 后面的目录。按上文选择控制器和资源、添加账号，再把这份托管放进现有队列。如果这款游戏已有普通托管，从队列里把该项换成含 UU 的托管即可。
2. 打开该账号的「任务队列」，先添加日常或应用预设，再添加并勾选「切换网易 UU 加速」。填写 UU 中的游戏全名。要核对区服时，填写 UU 显示的区服文字。UU 已打开时可留空程序路径。默认安装位置找不到时，再填 `uu.exe` 或 `uu_launcher.exe` 的完整路径。把 UU 放在前置任务区的第一项。[AUTO-MAS 前置任务的执行顺序](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/MaaFW/tools/embedded/runner_task.py#L873-L889)
3. **DMM 客户端**在「切换网易 UU 加速」里把 **「UU 加速后启动 DMM 游戏」** 选为「是」。新版默认选「是」，此前保存过「否」的托管需要改一次。取消勾选单独的「启动 DMM 游戏」前置任务。脚本会确认目标游戏正在加速，点击 UU 的「启动游戏」，等待对应游戏窗口出现，再交给 AUTO-MAS。学园偶像大师仍把 MaaGakumasu 自带的「启动游戏」留在普通任务的第一项。想通过 DMM 快捷方式启动时，把这个选项改为「否」，并保留单独的「启动 DMM 游戏」前置任务。[UU 加速和游戏启动说明](https://uu.baike.netease.com/zhinan/53.html)
4. 解锁桌面，保持 UU 窗口可见，关闭游戏本体后试跑一次。首次登录或遇到 DMM 更新提示时，在官方客户端处理后重试。若 Windows 显示「用户帐户控制」，核对应用和发布者后手动选「是」。启动脚本会在两分钟等待期内继续查找游戏窗口。[微软 UAC 说明](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/user-account-control/how-it-works)

在历史记录中先看「开始应用运行前设置」是否列出「切换网易 UU 加速」。UU 日志会列出本次模式。若显示 `UU 本次模式：仅加速`，核对是否已同步含 UU 托管、启用了前置任务，并把「UU 加速后启动 DMM 游戏」选为「是」。日志中的 `已点击 UU 的「启动游戏」` 表示点击已执行，后续的 DMM 日志会报告是否找到游戏窗口。若报告 `未找到匹配 MaaFW Win32 controller 的窗口`，核对前面的启动日志，以及学园偶像大师的「PC / DMM」或 Dot Abyss 的「DMM 游戏窗口 / 日文 DMM 客户端」选择。[AUTO-MAS 窗口查找逻辑](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/MaaFW/tools/embedded/runner_task.py#L1987-L2009)

切换游戏时，若 UU 弹出停止旧加速的确认框，日志会依次显示 `已请求停止 UU 的当前加速` 和 `已确认停止 UU 的旧加速`。重试时仍显示的停止确认框也会检查后处理。

取消勾选「切换网易 UU 加速」即可跳过加速。DMM 客户端仍可使用单独的「启动 DMM 游戏」前置任务。

### UU 停在首页或提示找不到游戏

更新安装目录中的 UU 脚本。以学园偶像大师为例，在仓库根目录运行以下命令。自定义过 `-ToolsRoot` 时，安装命令带上原路径。

```powershell
git pull --ff-only
& .\scripts\setup-windows.ps1 -Games gakumas -WithUu
```

沿用现有的「学园偶像大师（含 UU）」托管，在「基本信息 → 跟随来源目录」点「立即同步」后重试。更新后的脚本支持 UU 首页的同名游戏卡片和完整搜索结果页。游戏全名仍填写你在 UU 电脑版看到的卡片名称，包含实际显示的版本或平台后缀。

`Revert to STA COM threading mode` 是 pywinauto 的初始化提示。排查时继续看后面的 UU 日志，确认卡在定位搜索框、匹配游戏卡片，还是等待加速成功。
