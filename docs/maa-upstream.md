# Windows 用 AUTO-MAS 接入 Maa_bbb 和 MaaEnd

崩坏 3 和明日方舟：终末地可以交给 AUTO-MAS 的 MFW 托管运行。两个游戏都使用各自的官方发行包、识别素材、流程和 Agent。在 AUTO-MAS 选好控制器、资源和要跑的任务后，Daily Clear Hub 通过本机接口启动这份托管并确认完成结果。基础环境参见 [Windows 安装与运行](windows.md)。

## 1. 安装 AUTO-MAS

使用 [Windows 批量安装脚本](windows.md#1-一次准备所选游戏)后，可以直接打开输出的 AUTO-MAS 程序，跳到项目设置。以下命令用于单独下载及校验 Windows x64 便携版 v5.8.0。[AUTO-MAS v5.8.0](https://github.com/AUTO-MAS-Project/AUTO-MAS/releases/tag/v5.8.0)

```powershell
$Tools = Join-Path $env:USERPROFILE 'Games\DailyAutomation'
New-Item -ItemType Directory -Force $Tools | Out-Null

function Expand-VerifiedRelease($Url, $Sha256, $Destination) {
    $Zip = Join-Path $env:TEMP ([IO.Path]::GetFileName($Url))
    curl.exe --fail --location --retry 2 -o $Zip $Url
    if ($LASTEXITCODE -ne 0) { throw "下载失败：$Url" }
    if ((Get-FileHash -LiteralPath $Zip -Algorithm SHA256).Hash -ne $Sha256) {
        throw "SHA-256 校验失败：$Zip"
    }
    Expand-Archive -LiteralPath $Zip -DestinationPath $Destination
}

$MasRoot = Join-Path $Tools 'AUTO-MAS-v5.8.0'
if (-not (Test-Path -LiteralPath $MasRoot)) {
    Expand-VerifiedRelease `
        'https://github.com/AUTO-MAS-Project/AUTO-MAS/releases/download/v5.8.0/AUTO-MAS-v5.8.0-x64.zip' `
        '884a7b74da42ef837ca8ec8a1897f817839c77c201769155da18d870ccf73740' `
        $MasRoot
}
$MasExe = Get-ChildItem -LiteralPath $MasRoot -Filter 'AUTO-MAS.exe' -File -Recurse | Select-Object -First 1
if (-not $MasExe) { throw '找不到 AUTO-MAS.exe，请检查解压目录。' }
Start-Process -FilePath $MasExe.FullName -WorkingDirectory $MasExe.DirectoryName -Verb RunAs
```

确认 AUTO-MAS 界面已打开，再在另一个 PowerShell 验证本机后端。保持 AUTO-MAS 运行。为避免游戏输入冲突，在使用 Hub 的场合取消 AUTO-MAS 自身的定时、启动后自动运行和循环队列，也取消完成后关机等电源操作。Windows 防火墙保留对该端口的入站限制，Hub 只访问 `127.0.0.1`。[AUTO-MAS 用户指南](https://doc.auto-mas.top/docs/user-guide.html) · [本机后端接口源码](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/api/core.py#L102-L131)

```powershell
$Mas = 'http://127.0.0.1:36163'
Invoke-RestMethod -Uri "$Mas/api/core/health" |
    Select-Object ready, version, protocol, backgroundStatus
```

## 2. 安装并设置上游项目

使用批量脚本输出的项目目录，或在上面定义了 `$Tools` 和 `Expand-VerifiedRelease` 的 PowerShell 窗口单独下载。目录需包含 `interface.json` 及同包的资源和 Agent。只运行其中一款游戏时，执行对应一段。 [Maa_bbb v1.13.22](https://github.com/miaojiuqing/Maa_bbb/releases/tag/v1.13.22) · [MaaEnd v3.2.0](https://github.com/MaaEnd/MaaEnd/releases/tag/v3.2.0)

### 崩坏 3

```powershell
$Bh3Root = Join-Path $Tools 'Maa_bbb-v1.13.22'
if (-not (Test-Path -LiteralPath $Bh3Root)) {
    Expand-VerifiedRelease `
        'https://github.com/miaojiuqing/Maa_bbb/releases/download/v1.13.22/Maa_bbb-win-x86_64-v1.13.22.zip' `
        '5e8a297ea2775617b2274110f79af66bc37f5cb65ddbcb8ba4ed1600367ef935' `
        $Bh3Root
}
Get-ChildItem -LiteralPath $Bh3Root -Filter 'interface.json' -File -Recurse |
    Select-Object -ExpandProperty DirectoryName
```

在 AUTO-MAS 「脚本管理」新建 **MFW 脚本**，项目目录填上一步输出。给托管命名如 `Hub 崩坏3`，选择「桌面端」控制器及与你客户端语言和操作方式匹配的资源。默认简中键鼠用「键鼠操作」。PC 游戏保持 16:9，按 Maa_bbb 要求在游戏设置里关闭菜单提示。启用一个账号，在任务队列选择已经解锁的任务。可从作战任务领奖和邮件领取开始，再按需加入家园、舰团和减负任务。Windows 游戏启动方式可选接管已经运行的客户端，七款游戏一起运行时先在游戏中登录。[Maa_bbb 使用文档](https://github.com/miaojiuqing/Maa_bbb/blob/v1.13.22/README.md) · [控制器与资源声明](https://github.com/miaojiuqing/Maa_bbb/blob/v1.13.22/assets/interface.json)

### 明日方舟：终末地

```powershell
$EndfieldRoot = Join-Path $Tools 'MaaEnd-v3.2.0'
if (-not (Test-Path -LiteralPath $EndfieldRoot)) {
    Expand-VerifiedRelease `
        'https://github.com/MaaEnd/MaaEnd/releases/download/v3.2.0/MaaEnd-win-x86_64-v3.2.0.zip' `
        '2314044246733df849b7bc87c7fd99b8264f349eb947873701dea498d279b6b6' `
        $EndfieldRoot
}
Get-ChildItem -LiteralPath $EndfieldRoot -Filter 'interface.json' -File -Recurse |
    Select-Object -ExpandProperty DirectoryName
```

同样新建 **MFW 脚本**，项目目录填写 MaaEnd 的目录，给托管命名如 `Hub 终末地`。PC 客户端选择 `Win32-Front`（前台控制）和 v3.2.0 声明的「官服」资源。预先启动并登录游戏时，选择接管已运行窗口，在任务队列选日常奖励及需要的可选项。清理智、基建等使用 MaaEnd 对应任务和选项，先逐项试跑。Win32 前台控制期间保持桌面解锁并让出键鼠。[MaaEnd 使用文档](https://github.com/MaaEnd/MaaEnd/tree/v3.2.0/docs/zh_cn) · [控制器声明](https://github.com/MaaEnd/MaaEnd/blob/v3.2.0/assets/interface.json)

两款游戏都先等待 AUTO-MAS 的「运行环境」检查通过。账号任务可以在 AUTO-MAS 内逐项选择，也可在 MFW 的导入向导里复用受支持的外壳已保存配置。先从 AUTO-MAS 的调度台运行最小任务，确认资源、窗口和游戏账号正确。只需保持 AUTO-MAS 开着，Maa_bbb 和 MaaEnd 自带的窗口可关闭。[AUTO-MAS MFW 配置指南](https://doc.auto-mas.top/docs/script-guide/maafw.html) · [外壳配置导入接口](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/MaaFW/api.py#L364-L396)

## 3. 查询托管与账号 ID

同款游戏有多个托管且想保留它们时，可运行下列只读查询来选择目标。按名称和类型找到对应的 `ScriptId`。Maa_bbb 和 MaaEnd 两项都会显示 `MaaFWConfig`。[AUTO-MAS 托管查询](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/api/scripts/management.py#L303-L334)

```powershell
$Mas = 'http://127.0.0.1:36163'
$Scripts = Invoke-RestMethod -Uri "$Mas/api/scripts/get" -Method Post -ContentType 'application/json' -Body '{}'
if ($Scripts.code -ne 200) { throw $Scripts.message }
$Scripts.index | ForEach-Object {
    [pscustomobject]@{
        ScriptId = $_.uid
        Type     = $_.type
        Name     = $Scripts.data.($_.uid).Info.Name
    }
}
```

多账号托管可用下列命令取得指定账号的 `UserId`。不填写 `user_id` 时，上游运行这份托管中可运行的全部账号。[AUTO-MAS 账号查询](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/api/scripts/users.py#L249-L277)

```powershell
$ScriptId = Read-Host '粘贴托管 ScriptId'
$Body = @{ scriptId = $ScriptId } | ConvertTo-Json -Compress
$Accounts = Invoke-RestMethod -Uri "$Mas/api/scripts/user/get" -Method Post -ContentType 'application/json' -Body $Body
if ($Accounts.code -ne 200) { throw $Accounts.message }
$Accounts.index | ForEach-Object {
    $Info = $Accounts.data.($_.uid).Info
    [pscustomobject]@{ UserId = $_.uid; Name = $Info.Name; Enabled = $Info.Status }
}
```

## 4. 从 Hub 运行

回到 Hub 仓库根目录运行。只配置一款时，将命令末尾改成一项。

```powershell
& .\.venv\Scripts\python.exe .\main.py check --automas honkai3 endfield
& .\.venv\Scripts\python.exe .\main.py run --automas honkai3 endfield
```

每款只有一个匹配托管时，Hub 会自动选择。需保留多个托管时，在本机 `config.local.yaml` 为相应游戏设置 `backend: automas` 和上节取得的 `script_id`。如有多个启用账号，还可用 `user_id` 限制为其中一个。

`check` 查询本机托管和其实际加载的 MFW 项目。Hub 提交托管后根据本轮任务 ID 查询账号完成报告。超时或结果丢失时队列停止，用 AUTO-MAS 调度台核实状态。MFW 资源识别、Agent 缺失和游戏开始位置问题也在调度台检查。[AUTO-MAS 调度接口](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/api/dispatch.py#L122-L219) · [账号终态汇总](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/core/task_manager/manager.py#L2376-L2442)
