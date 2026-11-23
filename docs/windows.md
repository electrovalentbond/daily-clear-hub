# Windows 安装与运行

本指南使用 Windows 10/11 x64 和 PowerShell。游戏先安装并登录。各游戏的上游后端使用项目自带的识别素材，只需安装相应工具并配置游戏、设备与任务。选择内置 ok-script 流程时，可按本文的可选章节采集本机模板。

## 1. 安装系统依赖

在 PowerShell 中运行。Hub 使用 Python 3.12 x64。[WinGet 安装说明](https://learn.microsoft.com/zh-cn/windows/package-manager/winget/) · [ok-script 发行包](https://pypi.org/project/ok-script/1.0.154/)

```powershell
winget --version
winget install --exact --id Git.Git --source winget --accept-package-agreements --accept-source-agreements
winget install --exact --id Python.Python.3.12 --source winget --architecture x64 --accept-package-agreements --accept-source-agreements
winget install --exact --id 'Microsoft.VCRedist.2015+.x64' --source winget --accept-package-agreements --accept-source-agreements
```

如果找不到 `winget`，在 Microsoft Store 安装或更新「应用安装程序」。安装完后关闭 PowerShell，再打开新的窗口。[Microsoft 修复步骤](https://learn.microsoft.com/en-us/troubleshoot/windows-client/shell-experience/troubleshoot-apps-start-failure-use-windows-package-manager)

```powershell
git --version
py -3.12 -c "import struct, sys; print(sys.version); print(struct.calcsize('P') * 8)"
```

最后一行应输出 `64`。

## 2. 下载仓库与安装 Python 依赖

以下示例把代码下载到用户目录。其余命令在仓库根目录运行。如果路径含中文等字符且模板图片无法读取，把仓库和本地模板放到只含英文字母和数字的路径，例如 `C:\Games\daily-clear-hub`。

```powershell
Set-Location $env:USERPROFILE
git clone https://github.com/electrovalentbond/daily-clear-hub.git
Set-Location .\daily-clear-hub
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install 'PyYAML==6.0.3'
& .\.venv\Scripts\python.exe -m pip check
& .\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v
```

直接调用虚拟环境的 `python.exe` 即可。上游后端只额外要求各自的运行环境。单元测试检查配置、调度和结果解析，首次运行时逐款检查实际游戏操作。

## 3. 建立本机配置

```powershell
if (-not (Test-Path .\config.local.yaml)) {
    Copy-Item .\config.local.yaml.example .\config.local.yaml
}
notepad .\config.local.yaml
& .\.venv\Scripts\python.exe .\main.py plan
```

`config.yaml` 提供默认设置，`config.local.yaml` 覆盖本机设置。示例为七款游戏选好了上游后端，替换路径和托管 ID 后即可逐款检查。已有配置可按各游戏的示例合并。`plan` 显示游戏 ID 和当前后端。游戏默认关闭，`enabled: true` 将游戏加入队列。`schedule_order` 指定顺序，`timeout_sec` 指定单款游戏的等待上限。

### 崩坏3与终末地使用 AUTO-MAS

以 AUTO-MAS 运行 Maa_bbb 和 MaaEnd，两个游戏各自使用独立脚本配置与上游资源。先按 [AUTO-MAS 安装与任务配置](maa-upstream.md) 配好脚本 ID，再写入 `config.local.yaml`。

### 原神使用 BetterGI，绝区零使用一条龙

沿用上节安装的 AUTO-MAS。原神运行指定的 BetterGI 一条龙配置，绝区零运行对应实例下选中的一条龙任务。下载、安装、配置和检查命令见 [BetterGI 与绝区零一条龙配置](hoyo-upstream.md)。

### 公主连结国服使用 pcr-script

B 服的上游识别素材随源码提供。先设置雷电为 960×540 横屏，再按 [公主连结上游安装命令](pcr-upstream.md) 配置 Python、ADB 序列号及游戏内日程表。

### 星铁使用三月七小助手

如果使用星铁的 `march7th` 后端，现有的小助手安装目录里需有 `m7a.exe`。全新安装可以用下面的命令下载正式版并解压到用户目录。已有安装时直接复用其路径。[官方发行页](https://github.com/moesnow/March7thAssistant/releases/latest) · [安装与校验说明](https://github.com/moesnow/March7thAssistant/blob/v2026.11.22/assets/agent/skills/march7th-assistant/references/install.md)

```powershell
$M7ARoot = Join-Path $env:USERPROFILE 'Games\March7thAssistant'
if (Test-Path -LiteralPath $M7ARoot) { throw '请选择尚未使用的目录，或复用现有安装。' }
$Release = Invoke-RestMethod 'https://api.github.com/repos/moesnow/March7thAssistant/releases/latest'
$Asset = $Release.assets | Where-Object { $_.name -eq 'March7thAssistant_full.zip' }
if (-not $Asset -or $Asset.digest -notmatch '^sha256:[0-9a-f]{64}$') { throw '完整 ZIP 或校验值缺失。' }
$M7AZip = Join-Path $env:TEMP ('March7thAssistant_' + $Release.tag_name + '.zip')
Invoke-WebRequest -Uri $Asset.browser_download_url -OutFile $M7AZip -UseBasicParsing
if (('sha256:' + (Get-FileHash -LiteralPath $M7AZip -Algorithm SHA256).Hash) -ne $Asset.digest) {
    throw '三月七小助手压缩包 SHA-256 校验失败。'
}
Expand-Archive -LiteralPath $M7AZip -DestinationPath $M7ARoot
```

先打开小助手的图形界面，在首次启动流程中确认使用说明和星铁路径，并核对小助手内的日常设置。配置并退出窗口后，命令会查看状态和任务列表。`first_run_completed` 与 `game_path_exists` 应为 `true`。等待已有任务结束后再启动 Hub 队列。[三月七小助手命令行说明](https://m7a.top/assets/agent/skills/march7th-assistant/SKILL.md)

```powershell
$M7AExe = Get-ChildItem -LiteralPath $M7ARoot -File -Recurse -Filter 'm7a.exe' | Select-Object -First 1
if (-not $M7AExe) { throw '找不到 m7a.exe，请检查解压路径和小助手版本。' }
Push-Location $M7AExe.DirectoryName
try {
    Start-Process '.\March7th Launcher.exe' -Wait
    & .\m7a.exe --status
    & .\m7a.exe --list --json
} finally {
    Pop-Location
}
$M7AExe.FullName
```

把上述命令输出的完整路径写入 `config.local.yaml` 的 `executable`。路径可使用正斜杠，或放在 YAML 单引号中。

```yaml
games:
  starrail:
    backend: march7th
    executable: 'C:/Users/你的用户名/Games/March7thAssistant/m7a.exe'
    timeout_sec: 1800
```

Hub 用 `routine --non-interactive --after-finish None` 执行三月七小助手日常，具体操作依小助手配置。用管理员身份打开 PowerShell，在仓库目录运行以下命令。

```powershell
& .\.venv\Scripts\python.exe .\main.py check starrail
& .\.venv\Scripts\python.exe .\main.py run starrail
```

### 崩坏学园2使用 HKA

HKA 的上游适配基准为 Windows、MuMu、B 服、1600×900 横屏。启动并登录模拟器里的游戏，开启该实例的 ADB 调试。以下命令将已核对接口的 HKA 源码安装在独立的虚拟环境中。[HKA 快速开始与适配范围](https://github.com/lolineet/Honkai2Automation/blob/08052330d5294b53b5578416fbbd97c8aca3b180/README.md)

```powershell
$HkaRoot = Join-Path $env:USERPROFILE 'Games\Honkai2Automation'
New-Item -ItemType Directory -Force (Split-Path -Parent $HkaRoot) | Out-Null
git clone https://github.com/lolineet/Honkai2Automation.git $HkaRoot
git -C $HkaRoot checkout --detach 08052330d5294b53b5578416fbbd97c8aca3b180
py -3.12 -m venv (Join-Path $HkaRoot '.venv')
$HkaPython = Join-Path $HkaRoot '.venv\Scripts\python.exe'
$HkaConfig = Join-Path $HkaRoot 'config.json'
& $HkaPython -m pip install -e $HkaRoot
if (-not (Test-Path -LiteralPath $HkaConfig)) {
    Copy-Item (Join-Path $HkaRoot 'config.example.json') $HkaConfig
}
notepad $HkaConfig
```

在 HKA 的 `config.json` 中按实例设置 `emulator.adb_path`、`emulator.serial` 和 `emulator.package`，保存为 UTF-8 无 BOM。B 服包名示例为 `com.miHoYo.HSoDv2BiliBiliRelease`。JSON 里的 Windows 路径可写成 `C:/.../adb.exe`。示例配置含清体力、快捷战斗和派遣等任务，按你的目标核对 `tasks` 的 `enabled` 设置，先保留启动游戏与想验证的任务。[HKA 配置和命令](https://github.com/lolineet/Honkai2Automation/blob/08052330d5294b53b5578416fbbd97c8aca3b180/docs/configuration.md)

```powershell
Push-Location $HkaRoot
try {
    & $HkaPython -m hka --config $HkaConfig doctor
    & $HkaPython -m hka --config $HkaConfig plan
} finally {
    Pop-Location
}
```

检查连接和待办后，在 Hub 的 `config.local.yaml` 选择 `hka`，并替换下面的三个路径。

```yaml
games:
  bhxy2:
    backend: hka
    executable: 'C:/Users/你的用户名/Games/Honkai2Automation/.venv/Scripts/python.exe'
    project_dir: 'C:/Users/你的用户名/Games/Honkai2Automation'
    hka_config: 'C:/Users/你的用户名/Games/Honkai2Automation/config.json'
    timeout_sec: 1800
```

```powershell
& .\.venv\Scripts\python.exe .\main.py check bhxy2
& .\.venv\Scripts\python.exe .\main.py run bhxy2
```

## 4. 可选的内置 ok-script 流程

此节适用于选择 `backend: native` 的游戏。先在 Hub 环境安装 Windows 依赖。

```powershell
& .\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
& .\.venv\Scripts\python.exe -m pip check
```

### 原生 Windows 游戏

崩坏3 `honkai3`、崩坏：星穹铁道 `starrail`、绝区零 `zzz`、原神 `genshin` 和明日方舟：终末地 `endfield` 使用 Windows 窗口。通过游戏的官方客户端手动启动，登录到可操作的主界面。建议使用窗口模式，游戏分辨率要与配置及模板一致，默认 1920×1080。用以下命令按窗口名称查找游戏进程。

```powershell
Get-Process |
    Where-Object { $_.MainWindowHandle -ne 0 } |
    Select-Object ProcessName, Id, MainWindowTitle
```

配置中的 `exe` 为带 `.exe` 扩展名的游戏进程名。启动器和游戏窗口通常属于不同进程，按上面输出的窗口标题确认。游戏以管理员身份运行时，用同样权限打开 PowerShell，再切回仓库根目录。`templates` 可使用相对于仓库根目录的路径。`steps` 填写 `plan` 提供的步骤 ID，配置后会替换该游戏的默认步骤。以下覆盖配置只选崩坏3的邮件领奖。[ok-script 连接与截图说明](https://github.com/ok-oldking/ok-script/blob/master/docs/interface.md)

```yaml
games:
  honkai3:
    backend: native
    exe: BH3.exe
    resolution: [1920, 1080]
    templates: assets/local/honkai3/coco_annotations.json
    steps: [bh3_claim_mail]
```

### 雷电模拟器游戏

原生公主连结 `pcr`、崩坏学园2 `bhxy2` 使用 ADB。安装雷电 9，在模拟器内安装并登录对应渠道的游戏。在模拟器的设置页开启本地 ADB 调试，按提示重启实例。仅配 Windows 游戏或使用 HKA 上游时，可以跳过雷电安装。[雷电模拟器官网](https://www.ldmnq.com/) · [雷电 ADB 指南](https://jp.ldplayer.net/support/ldplayer-adb-command.html)

将 `$LdPlayerRoot` 改成实际安装目录。已打开模拟器时可直接查询设备。[雷电命令行指南](https://jp.ldplayer.net/support/ldconsole-command-line-guide.html)

```powershell
$LdPlayerRoot = 'C:\leidian\LDPlayer9'
$Adb = Join-Path $LdPlayerRoot 'adb.exe'
$LdConsole = Join-Path $LdPlayerRoot 'ldconsole.exe'
Test-Path $Adb
Test-Path $LdConsole
& $LdConsole list2
& $LdConsole launch --index 0
& $Adb devices -l
```

等待实例启动完成，只保留一个状态为 `device` 的 ADB 设备。下例的 `emulator-5554` 仅供参考。启动目标游戏后核对包名和实际显示尺寸。[ADB 命令说明](https://developer.android.com/tools/adb?hl=zh-cn)

```powershell
$Serial = 'emulator-5554'
& $Adb -s $Serial shell pm list packages -3
& $Adb -s $Serial shell dumpsys activity activities |
    Select-String 'topResumedActivity|mResumedActivity'
& $Adb -s $Serial shell wm size
& $Adb -s $Serial shell wm density
```

把序列号填入 `adb_serial`，`package:` 后面的包名填入 `package`，`resolution` 填 `[宽, 高]`。公主连结 B 服示例包名为 `com.bilibili.priconne`。崩坏学园2按所安装的渠道填写。两款游戏默认都使用 1280×720 横屏。可在雷电显示设置中设定相同尺寸，也可用下面的命令修改并重启实例。

```powershell
& $LdConsole quit --index 0
& $LdConsole modify --index 0 --resolution '1280,720,240'
& $LdConsole launch --index 0
& $Adb devices -l
```

重启后重新确认序列号，并打开游戏回到主界面。将以下公主连结配置写入 `config.local.yaml` 的 `games` 下，并换成实际序列号。

```yaml
games:
  pcr:
    backend: native
    adb_serial: 'emulator-5554'
    package: com.bilibili.priconne
    resolution: [1280, 720]
    templates: assets/local/pcr/coco_annotations.json
    steps: [pcr_collect_gifts]
```

原生模式处理已满足条件的领奖步骤。首次可用锁定版本自带的模板页采集并标注，以崩坏3为例先列出所选步骤需要的名称，再打开诊断窗口。每次换服、切换语言、改分辨率或游戏更新后，重新确认识别结果。[模板素材说明](../assets/README.md) · [ok-script 界面与开发工具](https://github.com/ok-oldking/ok-script/blob/master/docs/interface.md#模板素材管理)

```powershell
$Game = 'honkai3'
& .\.venv\Scripts\python.exe .\main.py plan --features $Game
& .\.venv\Scripts\python.exe .\main.py gui $Game --debug
```

在诊断窗口选择目标，确认能截到完整游戏画面。打开「模板」，用「截图」采集起点、入口、目的页及领奖状态。选中截图进入「标注」，以 `plan --features` 的名称给每个特征画框。首次截图会创建 COCO 文件，画框修改会自动写入。保留完整截图和自动保存的 COCO 文件，直接关闭标注和诊断窗口即可。

将这款游戏的 COCO 文件及其截图复制到默认模板目录。如修改过 `templates`，复制到该 JSON 对应目录。

```powershell
$Markup = ".\configs\$Game\diagnostics\ok_templates"
$Templates = ".\assets\local\$Game"
if (-not (Test-Path (Join-Path $Markup 'coco_annotations.json'))) {
    throw '请先在模板页截图并完成标注。'
}
New-Item -ItemType Directory -Force $Templates | Out-Null
Copy-Item -Path (Join-Path $Markup '*') -Destination $Templates
& .\.venv\Scripts\python.exe .\main.py check $Game
& .\.venv\Scripts\python.exe .\main.py run $Game
$LASTEXITCODE
```

`check` 检查配置、模板标注与图片文件。`run` 连接设备、核对目标并执行，全部所选步骤完成或确认没有待领取奖励时返回 `0`。先检查一次有奖励时的结果，再跑第二遍确认已领取状态。

## 5. 执行日常队列

按各后端的说明准备游戏、模拟器或上游工具，在本机配置开启已联调通过的游戏。AUTO-MAS 后端需要对应服务在本机运行。星铁内置邮件以已打开的触屏布局手机菜单为起点，绝区零内置邮件以已打开的游戏菜单为起点。原神及终末地从可操作的大世界画面开始，保留所选流程的默认游戏快捷键。以下命令按配置顺序运行队列。

```powershell
& .\.venv\Scripts\python.exe .\main.py check
& .\.venv\Scripts\python.exe .\main.py run
$LASTEXITCODE
```

也可显式选定几款游戏，命令按给出的顺序运行。显式 ID 可单独联调尚未加入队列的游戏。

```powershell
& .\.venv\Scripts\python.exe .\main.py check honkai3 pcr
& .\.venv\Scripts\python.exe .\main.py run honkai3 pcr
```

原生 ADB 会在唯一已连接的已配置设备上打开或切换到目标游戏。两款游戏都用原生后端时，请先登录、完成弹窗处理，并把两套模板和 `resolution` 校准到同一实例实际使用的尺寸，然后即可同队列运行。Windows 原生游戏的目标窗口保持打开，并留出前台键鼠供任务操作。

```powershell
& .\.venv\Scripts\python.exe .\main.py check pcr bhxy2
& .\.venv\Scripts\python.exe .\main.py run pcr bhxy2
```

自定义覆盖文件时，将 `--config` 写在子命令之前，并填写实际路径。

```powershell
& .\.venv\Scripts\python.exe .\main.py --config .\config.local.yaml run
```

## 6. 更新及排查

以下命令更新 Hub 并重新检查启用的游戏。若使用内置模式，另按第 4 节更新 `requirements.txt`。上游工具单独更新，优先使用相应配置指南中核对过的版本。

```powershell
Set-Location (Join-Path $env:USERPROFILE 'daily-clear-hub')
git pull --ff-only
& .\.venv\Scripts\python.exe -m pip install 'PyYAML==6.0.3'
& .\.venv\Scripts\python.exe -m pip check
& .\.venv\Scripts\python.exe .\main.py check
```

- `py -3.12` 找不到解释器时，运行 `py -0p` 查看已安装版本，安装 3.12 x64 后重新打开 PowerShell。
- 导入时提示 DLL 加载失败，检查 Python 位数、Visual C++ x64 运行库和 Windows 更新。[Visual C++ 运行库说明](https://learn.microsoft.com/zh-cn/cpp/windows/latest-supported-vc-redist)
- ADB 设备为空或显示 `offline` 时，确认实例已启动且已开启本地 ADB 调试，再运行 `& $Adb devices -l`。有 `unauthorized` 时，在模拟器中确认调试授权后重试。[Android 调试连接说明](https://developer.android.com/tools/adb?hl=zh-cn)
- Windows 找不到窗口时，确认已进入客户端、窗口未最小化，核对游戏进程名及运行权限。截图黑屏时，用窗口模式验证截图，再校验截图和模板的尺寸。[ok-script 截图排查](https://github.com/ok-oldking/ok-script/blob/master/docs/interface.md)
- 三月七小助手报首次使用、权限或已有任务在运行时，分别完成首次设置、使用管理员 PowerShell 或等待现有任务结束。查看上游运行状态可在小助手目录执行 `& .\m7a.exe --status`，查看最近一次输出可用 `& .\m7a.exe --follow latest`。[三月七小助手排查说明](https://github.com/moesnow/March7thAssistant/blob/v2026.11.22/assets/agent/skills/march7th-assistant/references/troubleshooting.md)
- 上游工具超时时 Hub 停止队列，先确认上游任务已经结束，再从输出找到要重跑的游戏。HKA 的报告和截图可在其 `runtime.run_dir` 对应目录查看，示例值为 `runs`。[HKA 配置和命令](https://github.com/lolineet/Honkai2Automation/blob/08052330d5294b53b5578416fbbd97c8aca3b180/docs/configuration.md)
- 日常步骤无法确认完成时，记录提示和当前游戏页面，在该游戏的真实界面补齐模板或检查导航，再执行相同的 `check` 和 `run` 命令。
