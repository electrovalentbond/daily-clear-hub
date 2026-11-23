# 公主连结国服上游运行

Daily Clear Hub 可以直接运行 [pcr-script](https://github.com/Gibberer/pcr-script/tree/d1eb2120599a5bc42ce934657f7788e1a8f0bfc3)。上游已有识别素材，使用 Windows x64 和 Python 3.12。以下步骤使用雷电模拟器中已经登录的哔哩哔哩国服客户端（包名 `com.bilibili.priconne`）。把上游脚本与 Hub 装在各自的虚拟环境中。首次运行需联网下载国服静态游戏数据。[上游数据加载实现](https://github.com/Gibberer/pcr-script/blob/d1eb2120599a5bc42ce934657f7788e1a8f0bfc3/pcrscript/masterdata.py#L184)

## 1. 安装上游和配置任务

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

## 2. 从 Hub 执行

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
