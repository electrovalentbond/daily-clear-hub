# Windows 安装与运行

推荐用 **AUTO-MAS 集中配置六款游戏**，再由 Hub 自动读取托管。崩坏 3、终末地和崩坏学园 2 使用 MaaFramework 项目。星铁、原神和绝区零使用 AUTO-MAS 的现成专项。公主连结 B 服也走同一条 Hub 命令，运行时识别模拟器并调用 pcr-script。这个模式使用上游识别素材，一般无需 `config.local.yaml`。

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

可以在 `-Games` 里只列需要的游戏。省略 `-Games` 会准备六款 AUTO-MAS 游戏。脚本下载并校验正式包、准备 Python 环境，再输出 AUTO-MAS 程序和各游戏的资源路径。原神的 BetterGI 安装器需打开一次，安装路径可用脚本给出的建议。已用过上游工具时，可以直接复用已有目录。若当前 PowerShell 的执行策略阻止脚本，可在该窗口运行 `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` 后重试。

工具默认放在 `$env:USERPROFILE\Games\DailyAutomation`。若用户名含中文或安装路径需要简化，可指定同一个新目录。自动识别公主连结时，把该目录一并传给 Hub。

```powershell
& .\scripts\setup-windows.ps1 -Games pcr,bhxy2 -ToolsRoot 'C:\Tools\DailyAutomation'
& .\.venv\Scripts\python.exe .\main.py plan --automas --tools-root 'C:\Tools\DailyAutomation'
```

## 2. 托管设置集中在 AUTO-MAS

打开脚本输出的 `AUTO-MAS.exe`，等待界面就绪。每款游戏只在 AUTO-MAS 建立一次托管，启用相应账号。已有匹配托管就直接复用。选择对应类型和安装目录，再按需要勾选任务。

- **崩坏 3、终末地、崩坏学园 2** 使用同一个「MFW 项目」入口，分别指向 Maa_bbb、MaaEnd、MaaBH2。崩坏 3 和终末地可接管已登录的 PC 游戏窗口。崩坏学园 2 绑定已登录的模拟器及实际渠道。已有 MaaEnd 专项也可识别。[崩坏 3 和终末地设置](maa-upstream.md#2-安装并设置上游项目) · [崩坏学园 2 设置](maabh2.md)
- **星铁** 首次打开三月七小助手保存日常设置。随后在 AUTO-MAS 选「HSR 脚本」，填写三月七目录并选择「原生配置」复用。仅使用三月七时，SRA 路径留空。AUTO-MAS 负责启动客户端时，指定含 `StarRail.exe` 的目录。[HSR 托管指南](https://doc.auto-mas.top/docs/script-guide/hsr.html)
- **原神、绝区零** 分别选 BetterGI 和绝区零一条龙专项，复用已保存的一条龙配置及账号实例。需要扫本时，在上游设置队伍、目标和资源消耗。[原神与绝区零首次配置](hoyo-upstream.md)
- **公主连结 B 服** 使用 `-Games pcr` 安装后，打开已登录的模拟器。Hub 选择唯一在线且安装了 `com.bilibili.priconne` 的 ADB 设备，并使用游戏内日程表、任务领奖和非体力礼物的默认组合。[公主连结 ADB 设置](pcr-upstream.md)

使用 Hub 调度时，关闭 AUTO-MAS 自身会同时启动游戏的定时或循环队列。游戏结束后的电源操作设为「无」。

## 3. 检查并运行

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
