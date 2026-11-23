# 公主连结国服上游运行

Daily Clear Hub 可以直接运行 [pcr-script](https://github.com/Gibberer/pcr-script/tree/d1eb2120599a5bc42ce934657f7788e1a8f0bfc3)。上游已有识别素材，使用 Windows x64 和 Python 3.12。以下步骤使用雷电模拟器中已经登录的哔哩哔哩国服客户端（包名 `com.bilibili.priconne`）。把上游脚本与 Hub 装在各自的虚拟环境中。首次运行需联网下载国服静态游戏数据。[上游数据加载实现](https://github.com/Gibberer/pcr-script/blob/d1eb2120599a5bc42ce934657f7788e1a8f0bfc3/pcrscript/masterdata.py#L184)

## 加入 AUTO-MAS 队列

在 Hub 仓库根目录运行以下命令。安装脚本下载指定提交的源码 ZIP 并核对 SHA-256，解压到 `%USERPROFILE%\Games\DailyAutomation\pcr-script` 下的版本目录。已安装的相同提交 Git 工作区也可复用。[GitHub 源码 ZIP 说明](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives)

```powershell
& .\scripts\setup-windows.ps1 -Games pcr
```

1. 使用 16:9 横屏并开启 ADB，在目标模拟器登录一次公主连结 B 服。上游基准为 **960×540**，匹配器会按画面缩放。复用 MaaBH2 的 1280×720 模拟器时，可先保持原尺寸完成单款联调。[上游模板缩放代码](https://github.com/Gibberer/pcr-script/blob/d1eb2120599a5bc42ce934657f7788e1a8f0bfc3/pcrscript/templates.py#L78-L108)
2. 在 AUTO-MAS「托管管理」新建「MFW脚本」，导入 `pcr AUTO-MAS project:` 后的目录。控制器选「安卓模拟器」，资源选「哔哩哔哩国服」，绑定模拟器实例。「游戏包名」留空即可，AUTO-MAS 启动模拟器后，pcr-script 会在该实例打开 B 服客户端。
3. 添加并启用一个账号，在「任务队列」添加「公主连结日常」，展开「日常事项」勾选游戏内日程表、任务领奖和非体力礼物。日程表按游戏内保存的安排运行，装备自动分解关闭。准备好后，把这个托管加入 [AUTO-MAS 调度队列](windows.md#3-在-auto-mas-一键运行)。

运行时使用 AUTO-MAS 当前绑定实例的 ADB 路径和序列号。上游会逐项核验结果，可在 AUTO-MAS 查看状态，在 pcr-script 目录的 `cache/daily/runs/` 查看详细报告。此托管提供三项日常，周常只运行游戏日程表本身已经包含的项目。

如果移动了 Hub 仓库或上游脚本目录，重新运行安装命令，然后在此托管启用「跟随来源目录」并点「立即同步」，使 AUTO-MAS 使用更新后的安装路径。[AUTO-MAS 来源同步说明](https://doc.auto-mas.top/docs/script-guide/maafw.html)

### 查看一次托管失败的原因

账号汇总只显示「停在 `DailyClearPcrRun`」时，打开 AUTO-MAS「历史记录」对应的运行详情，从附件打开 `run.worker.log`。搜索 `公主连结运行失败`、`失败原因`、`pcr-script 输出` 或 `[Agent:`。这些行可能包含本机路径、设备未连接、游戏未登录或识别失败等具体信息。已有托管更新 Hub 仓库后，下次运行就会使用新版结果日志。[AUTO-MAS Agent 日志转发](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/MaaFW/tools/core/runner/runner.py#L3119-L3158)

如果本轮已启动上游脚本，可以在安装输出中 `pcr project:` 对应的目录下打开 `cache/daily/runs/`，查看时间对应的 `console.log` 和 `summary.json`。[pcr-script 运行记录](https://github.com/Gibberer/pcr-script/blob/d1eb2120599a5bc42ce934657f7788e1a8f0bfc3/pcrscript/run_session.py)

## 可选的命令行调度

Hub 命令行使用已授权且安装了 B 服的唯一在线设备，按默认组合执行三项日常。

```powershell
& .\.venv\Scripts\python.exe .\main.py plan --automas pcr
& .\.venv\Scripts\python.exe .\main.py check --automas pcr
& .\.venv\Scripts\python.exe .\main.py run --automas pcr
```

查找 ADB 时，Hub 会优先使用同一工具目录下的 `platform-tools\adb.exe`，随后检查 PATH、Android SDK 和雷电 9 常用安装位置。可用 `adb devices -l` 查看已授权设备。若多个设备安装了 B 服，只保留目标设备在线，或在本机配置设置 `games.pcr.adb_serial`。工具装在其他目录时，在各子命令加 `--tools-root <目录>`。自定义日常任务可以沿用下面的手动配置。

## 手动安装与任务配置

```powershell
$PcrRoot = 'C:\Tools\pcr-script'
if (-not (Test-Path $PcrRoot)) {
    New-Item -ItemType Directory -Force (Split-Path -Parent $PcrRoot) | Out-Null
    git clone https://github.com/Gibberer/pcr-script.git $PcrRoot
}
git -C $PcrRoot checkout --detach d1eb2120599a5bc42ce934657f7788e1a8f0bfc3
py -3.12 -m venv (Join-Path $PcrRoot '.venv')
$PcrPython = Join-Path $PcrRoot '.venv\Scripts\python.exe'
& $PcrPython -m pip install -r (Join-Path $PcrRoot 'requirements.txt')
& $PcrPython -m pip check
$PcrConfig = Join-Path $PcrRoot 'daily_config.yml'
if (-not (Test-Path $PcrConfig)) {
    Copy-Item (Join-Path $PcrRoot 'runtime_defaults.yml') $PcrConfig
}
notepad $PcrConfig
```

在雷电模拟器中把游戏画面设为横屏 **960×540**，重启后登录并进入游戏首页。以下命令检查 ADB 设备与国服包名。修改安装路径和序列号为你本机的值。

```powershell
$LdRoot = 'C:\leidian\LDPlayer9'
$Adb = Join-Path $LdRoot 'adb.exe'
& $Adb devices -l
& $Adb -s emulator-5554 shell pm path com.bilibili.priconne
```

推荐按设备序列号绑定，修改上游 `daily_config.yml` 中的 `Extra`、`Gift` 和 `Task`。示例使用已保存的游戏内日程表、领取任务奖励与非体力礼物，关闭自动分解装备。

```yaml
Extra:
  dnpath: ''
  adb_path: 'C:/leidian/LDPlayer9/adb.exe'
  adb_serial: 'emulator-5554'
Gift:
  auto_dismantle: false
Task:
  1:
    - [schedule]
    - [get_quest_reward]
    - [get_gift, true]
```

首次使用前检查游戏中已保存的「日程表」。添加快捷扫荡、商店购买、角色强化等任务时，按上游任务指南核对预设、体力和货币设置。若使用雷电窗口驱动，可填写 `Extra.dnpath`，并只打开目标 0 号实例。上游命令从这一实例启动游戏，并使用第一个可见实例进行操作。[上游命令行指南](https://github.com/Gibberer/pcr-script/blob/d1eb2120599a5bc42ce934657f7788e1a8f0bfc3/docs/guides/command-line.md) · [上游任务指南](https://github.com/Gibberer/pcr-script/blob/d1eb2120599a5bc42ce934657f7788e1a8f0bfc3/docs/guides/tasks.md)

## 使用手动配置运行

在 Hub 的 `config.local.yaml` 合并以下设置。

```yaml
games:
  pcr:
    enabled: true
    backend: pcr_script
    executable: 'C:/Tools/pcr-script/.venv/Scripts/python.exe'
    project_dir: 'C:/Tools/pcr-script'
    pcr_config: 'C:/Tools/pcr-script/daily_config.yml'
    timeout_sec: 1800
```

在 Hub 仓库根目录运行。

```powershell
& .\.venv\Scripts\python.exe .\main.py check pcr
& .\.venv\Scripts\python.exe .\main.py run pcr
if ($LASTEXITCODE -ne 0) { Write-Warning '请检查上游的 cache\daily\runs 记录。' }
```

Hub 会读取上游最终 JSON 报告，并逐项展示状态。`complete`、`already_complete` 和 `unavailable` 是上游可核实的结论。`finished` 表示上游动作执行结束但缺少完成核验，常见于旧版快捷扫荡任务。出现识别、部分失败或超时时，查看上游目录里的 `cache/daily/runs/`，其中有任务报告和日志。[上游日常结果](https://github.com/Gibberer/pcr-script/blob/d1eb2120599a5bc42ce934657f7788e1a8f0bfc3/pcrscript/runtime.py#L167-L211)
