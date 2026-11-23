# Windows 安装与运行

在 **AUTO-MAS** 中配置七款游戏，放进同一个调度队列。日常使用时打开「调度中心」，选中队列并点「开始执行」。AUTO-MAS 会依次启动已配置的客户端和模拟器，执行各账号勾选的任务。识别素材随上游项目提供。

## 1. 一次准备所选游戏

使用 Windows 10/11 x64 和 PowerShell。游戏客户端先安装并登录。Windows 缺少 Git 或 Python 3.12 时，执行对应命令，安装完成后重新打开 PowerShell。[WinGet 安装说明](https://learn.microsoft.com/zh-cn/windows/package-manager/winget/)

```powershell
winget install --exact --id Git.Git --source winget --accept-package-agreements --accept-source-agreements
winget install --exact --id Python.Python.3.12 --source winget --architecture x64 --accept-package-agreements --accept-source-agreements
```

Visual C++ x64 运行库直接从微软下载。打开安装界面后按提示完成。如果安装器显示已装有相同或更新版本，可以继续下一步。[微软运行库下载说明](https://learn.microsoft.com/zh-cn/cpp/windows/latest-supported-vc-redist)

```powershell
$VcRuntime = Join-Path $env:TEMP 'vc_redist.x64.exe'
Invoke-WebRequest -UseBasicParsing -Uri 'https://aka.ms/vc14/vc_redist.x64.exe' -OutFile $VcRuntime -ErrorAction Stop
Start-Process -FilePath $VcRuntime -Wait
```

首次克隆，或更新已有仓库。从仓库根目录运行批量安装脚本。

```powershell
$Hub = Join-Path $env:USERPROFILE 'daily-clear-hub'
if (-not (Test-Path (Join-Path $Hub '.git'))) {
    git clone https://github.com/electrovalentbond/daily-clear-hub.git $Hub
} else {
    git -C $Hub pull --ff-only
}
Set-Location $Hub
& .\scripts\setup-windows.ps1 -Games honkai3,starrail,zzz,genshin,pcr,bhxy2,endfield
```

可以在 `-Games` 里只列需要的游戏。脚本会校验下载包，并输出 AUTO-MAS 程序和各游戏的项目路径。原神的 BetterGI 安装器需运行一次，可以按脚本输出的建议目录安装。已安装的上游工具可以复用。若当前 PowerShell 的执行策略阻止脚本，可在该窗口运行 `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` 后重试。

如果需要通过代理下载，在启动脚本前设置当前 PowerShell 窗口的代理。把 `7890` 换成实际 HTTP 或混合代理端口。

```powershell
$env:HTTPS_PROXY = 'http://127.0.0.1:7890'
& .\scripts\setup-windows.ps1 -Games honkai3,starrail,zzz,genshin,pcr,bhxy2,endfield
```

遇到 `curl 56` 等连接中断时，脚本会自动重试。若仍中断，保留工具目录 `Downloads` 里的 `.part` 文件并重跑同一条命令。支持续传的服务器会从已有字节继续。安装包和公主连结的源码 ZIP 通过 SHA-256 校验后才会解压或交给安装器。解压失败后也可直接重跑，脚本会复用 `Downloads` 中已校验的 ZIP。

工具默认放在 `$env:USERPROFILE\Games\DailyAutomation`。以前安装时传过 `-ToolsRoot`，重跑时沿用原值。已有七款的上游工具时，更新仓库后只需重新准备公主连结的 MFW 项目。若安装输出中已出现 `pcr AUTO-MAS project:`，可以直接使用该目录。

```powershell
git pull --ff-only
& .\scripts\setup-windows.ps1 -Games pcr
```

## 2. 在 AUTO-MAS 选择任务和游戏启动方式

打开脚本输出的 `AUTO-MAS.exe`。首次启动需联网准备运行环境。在「托管管理 → 新建托管」为每款游戏选择下列类型。已有托管可直接编辑。每个托管都要「添加账号」并确认账号已启用。单账号可先在游戏中登录一次，使用客户端保存的登录状态。遇到重新登录或验证码提示时，在客户端完成后重试。[AUTO-MAS 使用指南](https://doc.auto-mas.top/docs/user-guide.html)

### 四款 MFW 游戏

选「MFW脚本」并导入脚本输出、含 `interface.json` 的项目目录。托管页选控制器和资源，等待「运行环境」准备完成。进入账号的「任务队列」点「添加任务」并选择要执行的项目。单项设置的「运行日」限定星期几。希望周常成功一次后本周自动跳过，可以在托管的「运行配置 → 每周完成后跳过」选中对应任务。[MFW 官方指南](https://doc.auto-mas.top/docs/script-guide/maafw.html)

两款模拟器游戏可以共用同一个雷电实例。在左侧「模拟器管理」点「自动搜索模拟器」并导入，再在两个托管的「控制配置」选同一个「模拟器」和「模拟器实例」，各自填写游戏包名。[模拟器管理](https://doc.auto-mas.top/docs/advanced-features/emulator.html)

- **崩坏 3** 导入 Maa_bbb，选择「桌面端」和匹配的资源，简中键鼠使用「键鼠操作」。到「控制配置 → PC 游戏启动方式」选择「由 MAS 启动和关闭游戏」，再选客户端的「游戏可执行文件」。任务可从作战任务领奖和邮件领取开始。[Maa_bbb 设置](maa-upstream.md#崩坏-3)
- **终末地** 导入 MaaEnd，PC 官服选择 `Win32-Front` 和「官服」。在「PC 游戏启动方式」选择「由 MAS 启动和关闭游戏」，指定 `Endfield.exe`。任务队列可添加日常奖励、清理智和基建。若客户端要求通过官方启动器，改用「MaaEnd脚本」托管，选择已有 MaaEnd 目录和 `Endfield.exe`，将「游戏启动方式」设为「启动器启动」，再把这个托管加入同一队列。前台控制期间保持桌面解锁。[MaaEnd 设置](maa-upstream.md#明日方舟终末地) · [官方启动器设置](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/frontend/src/views/EditView/Script/components/MaaEndLauncherSection.vue)
- **崩坏学园 2** 导入 MaaBH2，选「雷电模拟器」和「默认」，绑定已登录的模拟器实例并填写对应渠道包名。B 服用 `com.miHoYo.HSoDv2BiliBiliRelease`。AUTO-MAS 会启动绑定的游戏，任务队列可以从「10. 每日每周任务奖励领取」开始。[MaaBH2 设置](maabh2.md)
- **公主连结 B 服** 导入 `pcr AUTO-MAS project:` 后面的目录，选「安卓模拟器」和「哔哩哔哩国服」，绑定已登录的模拟器实例。「游戏包名」留空即可，pcr-script 会启动 B 服客户端。在账号的任务队列添加「公主连结日常」，展开「日常事项」勾选日程表、任务领奖和非体力礼物。日程表的扫荡项目和资源用量沿用游戏内设置。[公主连结配置](pcr-upstream.md)

### 三款专项游戏

- **星铁** 先打开一次三月七小助手并保存，让它生成 `config.yaml`。新建「HSR脚本」，「三月七路径」指向含 `March7th Assistant.exe` 的目录，SRA 路径可留空。「由 MAS 启动和关闭游戏」选「是」，「游戏路径」选含 `StarRail.exe` 的文件夹。账号选「独立配置」，在「任务配置」勾选「日常与奖励」、需要的体力与周常模块，并选择三月七引擎。历战余响可设开始日。差分宇宙与货币战争共用本周完成记录。[HSR 托管指南](https://doc.auto-mas.top/docs/script-guide/hsr.html)
- **原神** 安装并打开一次 BetterGI，在其「启动」页启用「同时启动原神」和「自动进入游戏」，浏览选择游戏客户端，然后退出 BetterGI。新建「BetterGI脚本」，「BetterGI 路径」指向含 `BetterGI.exe` 的目录。账号用「独立配置」，在「任务配置」勾选领取每日奖励、邮件和需要的体力项目。高级设置可从账号页的「配置 BetterGI」进入。队列运行时，BetterGI 根据保存的启动配置打开原神。[BetterGI 托管指南](https://doc.auto-mas.top/docs/script-guide/bettergi.html) · [BetterGI 启动设置](https://www.bettergi.com/quickstart.html)
- **绝区零** 先打开一次 `OneDragon-RuntimeLauncher.exe` 完成初始化，再退出一条龙。新建「ZZZ-OD脚本」，指定包含该启动器的「ZZZ-OD 安装目录」。单账号选「原生」，在实例管理中把目标实例「设为活跃」，「运行实例」选「仅运行当前」，启动器选「集成」或「自动」。在账号页填写实例的 `ZenlessZoneZero.exe` 完整路径，在「任务配置」启用录像店、刮卡、活跃度领奖等日常。需要周常时可在同页设置恶名狩猎计划。「游戏结束后操作」选「无」，一条龙会用实例的路径启动游戏。[原神与绝区零首次配置](hoyo-upstream.md) · [绝区零任务配置](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/frontend/src/views/EditView/User/ZzzOdUserEdit.vue#L575-L605)

## 3. 在 AUTO-MAS 一键运行

1. 打开「调度队列」，点「新建队列」，命名为 `七款游戏日常`。队列类型选「定时队列」。只想手动启动时，「启动时运行」选「从不」，「定时运行」选「否」，「任务完成后」选「无动作」。
2. 点「添加任务」并逐个选择七个托管。可拖动调整顺序。每行的「运行周几」决定整个托管在哪些天运行，包含日常的托管可以勾选全周。
3. 打开「调度中心」，在「选择任务项」下拉框选刚才的队列，确认「本次运行范围」包含要跑的账号，然后点「开始执行」。AUTO-MAS 按顺序执行，并在日志和历史记录展示结果。首次可在每个游戏关闭后测试对应托管能否自动打开游戏，再运行整队列。

需要每天定时执行时，把队列的「定时运行」设为「是」，在「定时列表 → 添加定时」设置执行周期和时间，并把该行设为「启用」。AUTO-MAS 需保持运行，桌面类任务需要可用的 Windows 桌面。[AUTO-MAS 队列说明](https://doc.auto-mas.top/docs/task-scheduler.html) · [调度中心启动按钮](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/frontend/src/views/scheduler/SchedulerTaskControl.vue#L140-L164)

## 可选的 Hub 命令行调度

如果要用 PowerShell 启动任务，Hub 仍提供命令行入口。使用这个入口时，让 AUTO-MAS 中的队列保持手动并停止其他正在运行的队列，避免两个调度同时操作客户端。工具装在自定义目录时，在 Hub 子命令上加 `--tools-root <原安装目录>`。

先用 `plan` 查看 Hub 识别到了哪些托管和设备，再检查和运行。保持 AUTO-MAS 打开。可以先显式指定一款游戏试跑。

```powershell
& .\.venv\Scripts\python.exe .\main.py plan --automas
& .\.venv\Scripts\python.exe .\main.py check --automas honkai3
& .\.venv\Scripts\python.exe .\main.py run --automas honkai3
```

单款验证后，用下面的命令运行全部发现的游戏。计划里显示的托管名来自 AUTO-MAS。可以在命令末尾指定游戏 ID 来限制本次队列。公主连结单独运行时可以省去启动 AUTO-MAS。

```powershell
& .\.venv\Scripts\python.exe .\main.py check --automas
& .\.venv\Scripts\python.exe .\main.py run --automas
$LASTEXITCODE
```

`--automas` 根据实时发现的项目选游戏。尚未配置的项目会在输出里显示，显式指定的游戏缺失时改为报错。游戏 ID 为 `honkai3`、`starrail`、`zzz`、`genshin`、`pcr`、`bhxy2`、`endfield`。

同款游戏有多个托管时，Hub 会列出名称和 ID。可以直接在 AUTO-MAS 整理托管，或在本机 YAML 里只为该游戏填写一个 `script_id`。保留旧配置的有效 ID 或 `user_id` 可继续绑定指定托管或账号。只有改过本机端口才需要传 `--automas-port`，默认为 36163。[查询与手动指定托管 ID](maa-upstream.md#3-查询托管与账号-id)

## 可选的手动配置与诊断

已有 `config.local.yaml` 可继续用 `plan`、`check`、`run`，并省略 `--automas`。手动字段见 [config.local.yaml.example](../config.local.yaml.example)。三月七和 HKA 的独立配置分别参见[三月七说明](https://github.com/moesnow/March7thAssistant/blob/v2026.11.22/assets/agent/skills/march7th-assistant/SKILL.md)和[HKA 命令指南](https://github.com/lolineet/Honkai2Automation/blob/08052330d5294b53b5578416fbbd97c8aca3b180/docs/configuration.md)。

使用内置 `backend: native` 时，安装 Windows 依赖并按游戏采集模板。可在本机 YAML 设定登录窗口或 ADB 设备。以崩坏 3 为例：

```powershell
& .\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
& .\.venv\Scripts\python.exe .\main.py plan --features honkai3
& .\.venv\Scripts\python.exe .\main.py gui honkai3 --debug
```

截图、标注与复制素材的命令见[模板手册](../assets/README.md)。遇到上游失败和超时，先在 AUTO-MAS 调度台或 pcr-script 的 `cache/daily/runs` 查本次记录。可在 Hub 仓库运行以下测试：

```powershell
& .\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v
```
