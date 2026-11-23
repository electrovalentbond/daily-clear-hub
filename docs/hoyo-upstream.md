# 原神和绝区零上游日常

两个游戏通过 AUTO-MAS 使用上游自带的客户端识别资源。先[安装 AUTO-MAS](maa-upstream.md#1-安装-auto-mas)，保留 AUTO-MAS 在本机运行。安装并登录两款游戏的 Windows 客户端，然后按需要配置下面任意一款。

## 原神 · BetterGI

批量安装脚本会准备 BetterGI 0.67.0 安装器。已有安装器或已安装该版本时，直接使用对应文件或原目录。也可按以下命令单独下载。[BetterGI 0.67.0 发布页](https://github.com/babalae/better-genshin-impact/releases/tag/0.67.0)

```powershell
$BetterGiSetup = Join-Path $env:TEMP 'BetterGI.Install.0.67.0.exe'
$BetterGiUrl = 'https://github.com/babalae/better-genshin-impact/releases/download/0.67.0/BetterGI.Install.0.67.0.exe'
Invoke-WebRequest -Uri $BetterGiUrl -OutFile $BetterGiSetup
if ((Get-FileHash -LiteralPath $BetterGiSetup -Algorithm SHA256).Hash -ne 'b065a7301d44bb818a313e07513b5a90d356003a5115a83749246a4b03fa2308') {
    throw 'BetterGI 安装包 SHA-256 校验失败。'
}
Start-Process -FilePath $BetterGiSetup -Wait
```

1. 在安装器里选安装目录，例如 `C:\Tools\BetterGI`。打开 BetterGI，在已登录的原神窗口上完成首次配置。
2. 在 BetterGI 的「一条龙」新建或选定一份日常配置，启用想运行的任务，例如每日奖励和纪行。需要清树脂时，在同一配置里完成副本或地脉花、队伍、战斗策略等设置。把完成后操作设为无电源操作，保存配置。退出 BetterGI 后继续。
3. 在 AUTO-MAS 的「托管管理 → 新建托管」选择 BetterGI，根目录选择含 `BetterGI.exe` 的目录。添加并启用一个账号。首次建议用「原生配置」复用刚保存的配置，在「一条龙名称」选准确的名字。需要独立配置时，在账号编辑页改选「独立配置」，用「配置 BetterGI」打开并保存 `MAS独立配置`。[AUTO-MAS 的 BetterGI 配置说明](https://doc.auto-mas.top/docs/script-guide/bettergi.html)

BetterGI 有些领奖步骤会报告流程结束但无法确认到账。AUTO-MAS 核对本次一条龙的结束日志和子步骤错误。账号显示「部分失败」时，Hub 会将其计作未完成，具体失败步骤可在 AUTO-MAS 调度结果及 BetterGI 的 `log` 中查阅。[BetterGI 的结果判定](https://github.com/babalae/better-genshin-impact/blob/0.67.0/BetterGenshinImpact/GameTask/Common/Job/ClaimDailyRewardsTask.cs#L45-L71) · [AUTO-MAS 分步判定](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/BetterGI/AutoProxy.py#L2069-L2084) · [AUTO-MAS 最终账号数](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/core/task_manager/manager.py#L2431-L2437)

## 绝区零 · 一条龙

批量脚本会解压 v2.6.1 的完整包，其中包含集成启动器、运行依赖和模型。已有含 `OneDragon-RuntimeLauncher.exe` 的目录可以复用，也可按以下命令单独安装。[一条龙 v2.6.1 发布页](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon/releases/tag/v2.6.1)

```powershell
$ZzzInstall = 'C:\Tools\ZZZ-OD'
if (Test-Path -LiteralPath $ZzzInstall) {
    throw '请选择尚未使用的目录，或直接复用现有安装。'
}
$ZzzAsset = 'ZenlessZoneZero-OneDragon-v2.6.1-WithRuntime-Full.zip'
$ZzzZip = Join-Path $env:TEMP $ZzzAsset
$ZzzUrl = "https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon/releases/download/v2.6.1/$ZzzAsset"
Invoke-WebRequest -Uri $ZzzUrl -OutFile $ZzzZip
if ((Get-FileHash -LiteralPath $ZzzZip -Algorithm SHA256).Hash -ne 'c83607cf8966db4b440e1e1d4f38fad47099b1977cf41f7381ba85857779ce57') {
    throw '绝区零一条龙压缩包 SHA-256 校验失败。'
}
Expand-Archive -LiteralPath $ZzzZip -DestinationPath $ZzzInstall
$ZzzLauncher = Get-ChildItem -LiteralPath $ZzzInstall -Recurse -File -Filter 'OneDragon-RuntimeLauncher.exe' | Select-Object -First 1
if (-not $ZzzLauncher) { throw '找不到集成启动器，请检查压缩包和解压目录。' }
$ZzzLauncher.DirectoryName
Start-Process -FilePath $ZzzLauncher.FullName -WorkingDirectory $ZzzLauncher.DirectoryName -Wait
```

1. 首次打开一条龙时等待初始化，在设置里确认游戏路径和区服，选择已登录的账号实例。勾选要运行的一条龙任务，如录像店经营、刮卡和活跃度领奖。需要清电量时另外配置上游刷本计划和编队。把「结束后」设为「无」，保存并退出一条龙窗口。
2. 在 AUTO-MAS 的「托管管理 → 新建托管」选择「绝区零一条龙（ZZZ-OD）」。根目录填写上面命令输出的目录。添加并启用一个账号，在「配置来源」选择直接使用一条龙原生配置，启动器选择「集成」或「自动」。
3. 单账号首次联调时，将「运行实例」设为「仅运行当前」，并核对当前活跃实例。核对 AUTO-MAS 中显示的任务开关与一条龙一致。已有的原生运行记录可以复用，一条龙会按已完成状态跳过相应任务。[启动器选项](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/ZzzOd/launchers.py#L28-L50) · [原生配置与实例](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/frontend/src/views/EditView/User/ZzzOdUserEdit.vue#L133-L162)

AUTO-MAS 会结合本轮的一条龙日志与任务记录判断结果。启动后直接退出会显示失败；当天任务均已完成时，需要一条龙确认整轮正常结束才会报告完成。[绝区零终态判定](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/ZzzOd/AutoProxy.py#L1169-L1247)

## 从 Hub 运行

在 Hub 仓库根目录检查两个已保存的专项。只配置一款时，在命令末尾传该游戏的 ID。

```powershell
& .\.venv\Scripts\python.exe .\main.py plan --automas genshin zzz
& .\.venv\Scripts\python.exe .\main.py check --automas genshin zzz
& .\.venv\Scripts\python.exe .\main.py run --automas genshin zzz
```

同款游戏有多个托管时，可按[查询托管与账号 ID](maa-upstream.md#3-查询托管与账号-id)指定一个。流程中止或超时时，在 AUTO-MAS 调度台核实本次任务状态。
