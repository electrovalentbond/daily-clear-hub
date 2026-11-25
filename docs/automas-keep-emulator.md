# AUTO-MAS 日常结束后保留雷电模拟器

要让崩坏学园 2 和公主连结在调度结束后保持打开，在两个托管的「控制配置」选各自的「保留雷电」设备，并把队列的「任务完成后」设为「无动作」。两款游戏用不同的雷电实例时，在运行前打开两个实例。[调度队列设置](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/frontend/src/views/queue/index.vue#L180-L197)

AUTO-MAS v5.8.0 的原生雷电和「模拟器 2.0」绑定会在每个 MFW 托管结束时关闭对应实例。队列的「无动作」只控制整条队列结束后的关机、休眠等操作。保留模式使用「通用」设备，AUTO-MAS 在日常完成、失败、停止或重试时只清理 ADB 监视进程，模拟器和当前游戏可继续使用。[MFW 托管收尾](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/MaaFW/tools/embedded/runner_task.py#L1119-L1121) · [通用模拟器实现](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/utils/common/emulator/general.py#L104-L121)

## 两款游戏分开使用雷电实例

如果 AUTO-MAS 已登记两款游戏各自的 `127.0.0.1` 保留绑定，可以直接做第 3、4 步。

1. 先手动打开两个雷电实例。在各自的「设置 → 其他设置 → ADB 调试」选择「开启本地连接」。改过设置时保存并重启对应实例。确认已进入 Android 桌面，保持 AUTO-MAS 打开并等现有队列结束。[雷电 ADB 设置](https://www.ldplayer.net/blog/introduction-to-version-4.0.37-and-3.102-features.html)
2. 在 Hub 仓库根目录运行以下命令。将 `$Adb` 改成雷电自带的 `adb.exe` 路径，根据 `list2` 第一列的编号和第二列的标题找到两个游戏的实例，把示例中的 `0`、`1` 换成实际编号。

   ```powershell
   git pull --ff-only
   $Adb = 'C:\LDPlayer\LDPlayer9\adb.exe'
   & (Join-Path (Split-Path -Parent $Adb) 'ldconsole.exe') list2
   & .\.venv\Scripts\python.exe -m scripts.automas_keep_emulator register --adb $Adb --ld-index 0 --ld-index 1
   ```

   如果雷电目录只有 `dnconsole.exe`，用它取代 `ldconsole.exe` 查看编号。使用自定义 AUTO-MAS 端口时，登记命令加 `--port`。两款游戏共用实例时，只登记一次该编号。

3. 刷新 AUTO-MAS。在两个游戏各自的「托管管理 → 控制配置」里，「模拟器」选择命令输出的「Daily Clear Hub 保留雷电（…）」，「模拟器实例」粘贴对应输出的整段文字。默认配置下，编号 `0` 对应 `track-devices | 127.0.0.1:5555`，编号 `1` 对应 `track-devices | 127.0.0.1:5557`。按实际窗口对应关系选择，点击输入框外保存。[通用实例输入框](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/frontend/src/views/EditView/Script/components/EmulatorInstanceField.vue#L14-L22)
4. 在「调度队列」选择现有队列，将「任务完成后」设为「无动作」。在「调度中心」手动执行时，也确认右上角「任务完成后电源操作」为「无动作」。[队列设置](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/frontend/src/views/queue/index.vue#L180-L197) · [调度中心电源选项](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/frontend/src/views/scheduler/index.vue#L9-L26)

以后执行队列前打开对应雷电实例即可。公主连结的日常项目会启动 B 服游戏。崩坏学园 2 可以事先进入游戏主页，或在 MaaBH2 账号的任务队列开头添加「启动游戏」并选自己的渠道。[MaaBH2 启动选项](https://github.com/freeze-12/MaaBH2/blob/bd2f83a6dbd6dc5516a79e910ced08b745e8eb70/interface.json)

## 找不到指定的 ADB 实例

旧托管的 `track-devices | emulator-5554` 和 `track-devices | emulator-5556` 依赖 ADB 设备发现。如果报告 `device … not found`，按上面的步骤改为 `--ld-index` 登记的 `127.0.0.1:端口`。AUTO-MAS 运行时会尝试连接该地址。在日志里查「ADB 设备已就绪」确认连接完成。[雷电 ADB 端口](https://jp.ldplayer.net/support/ldconsole-command-line-guide.html) · [MaaFW 就绪检查](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/MaaFW/tools/core/runner/runner.py#L2616-L2688)

如果默认端口连不上，先在雷电多开管理器手动打开对应实例，检查「开启本地连接」，再试以下命令。即使原生雷电启动报 `InvalidComApi`，也可以直接检查已经打开的窗口。用登记输出的实际端口替换 `5557`。[Android ADB 命令](https://developer.android.com/tools/adb)

```powershell
& $Adb connect 127.0.0.1:5557
& $Adb -s 127.0.0.1:5557 get-state
```

返回 `device` 后可用以下命令登记地址。若已知实例使用其他本地端口，把 `--serial` 的值换成实际地址。之前原生托管跑通的记录中，「ADB 连接方式」会列出 `地址=` 和 `ADB 路径=`，可用于核对。如果设备已就绪但 AUTO-MAS 仍连接失败，在历史记录打开本次 `run.worker.log`，确认日志的地址与刚才验证的端口一致。[AUTO-MAS ADB 日志与检查](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/MaaFW/tools/core/runner/runner.py#L2302-L2319)

```powershell
& .\.venv\Scripts\python.exe -m scripts.automas_keep_emulator register --adb $Adb --serial 127.0.0.1:5557
```

## 查看普通 ADB 截图和恢复原绑定

通用连接使用普通 ADB 截图。部分雷电游戏的画面可能是黑屏或缺少渲染层。遇到已进游戏但识别始终超时的情况，在游戏主页保持可见，用登记时输出的本机地址查看实际截图。[AUTO-MAS 截图方式实现与雷电渲染说明](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/MaaFW/tools/embedded/runner_task.py#L1862-L1886)

```powershell
$Image = & .\.venv\Scripts\python.exe -m scripts.automas_keep_emulator screenshot --adb $Adb --serial 127.0.0.1:5555
if ($LASTEXITCODE -eq 0) { Invoke-Item -LiteralPath $Image }
```

截图显示异常，或想让 AUTO-MAS 自动启动和关闭雷电时，把游戏「控制配置」中的「模拟器」和「模拟器实例」换回原先的原生雷电设备。已有「模拟器 2.0」或雷电配置仍可直接选用。所有相关托管都换回原设备后，可以在「模拟器管理」中删除「保留雷电」条目。
