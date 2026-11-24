# AUTO-MAS 日常结束后保留雷电模拟器

AUTO-MAS v5.8.0 的原生雷电和「模拟器 2.0」绑定会在 MFW 托管结束时关闭模拟器。若想保留窗口，可以新增一个「通用」模拟器连接已打开的实例。此配置让 AUTO-MAS 管理 ADB 的设备监视进程，日常完成、失败、停止或重试时只会清理该监视进程。雷电由你手动启动，可以在日常结束后继续操作。[AUTO-MAS 的 ADB 生命周期说明](https://doc.auto-mas.top/developer/maafw/tradeoffs.html) · [通用模拟器实现](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/utils/common/emulator/general.py) · [Android ADB 命令](https://android.googlesource.com/platform/packages/modules/adb/+/refs/tags/android-vts-17.0_r1/docs/user/adb.1.md)

## 添加保留模式

1. 按 [Windows 手册](windows.md) 完成环境和托管配置。手动打开雷电对应的多开实例，等待进入 Android 桌面，在模拟器设置启用 ADB 本地连接。保持 AUTO-MAS 运行，等现有队列结束。
2. 在 Hub 仓库根目录运行以下命令。将 `$Adb` 改成实际雷电安装目录下的 `adb.exe` 路径。

   ```powershell
   $Adb = 'C:\LDPlayer\LDPlayer9\adb.exe'
   & .\.venv\Scripts\python.exe -m scripts.automas_keep_emulator register --adb $Adb
   ```

   如果提示发现多个本地模拟器，按下文分别指定序列号。非默认本机 AUTO-MAS 端口用 `--port` 指定。

3. 刷新 AUTO-MAS，再进入公主连结或崩坏学园 2 的「托管管理 → 控制配置」。「模拟器」选命令输出的「Daily Clear Hub 保留雷电（…）」，把它输出的「模拟器实例」整段粘到对应输入框，例如 `track-devices | emulator-5554`。点击输入框外保存。两款游戏共用一个已登录的雷电实例时，可选同一个设备并粘贴同一段实例。新增设备也会出现在原有「模拟器 2.0」配置所在的模拟器列表中。[模拟器类型选择](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/frontend/src/views/Emulator.vue#L60-L69) · [通用实例输入框](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/frontend/src/views/EditView/Script/components/EmulatorInstanceField.vue#L14-L22)

每次运行前确认雷电已经打开。公主连结的日常项目会启动 B 服游戏。崩坏学园 2 保留模式下可以先手动进入游戏主页，也可以在 MaaBH2 队列中添加「启动游戏」并选正确渠道。先各跑一次低风险任务，例如领奖，两款游戏共用实例时按队列顺序运行。

## 两款游戏分开使用雷电实例

在各自的雷电窗口打开游戏，查看两个窗口对应的 ADB 序列号。用你机器上的实际序列号替换以下示例。[雷电多实例 ADB 指南](https://jp.ldplayer.net/support/ldplayer-adb-command.html) · [Android ADB 设备查询](https://developer.android.com/tools/adb#query-devices)

```powershell
& $Adb devices -l
& $Adb -s emulator-5554 shell dumpsys window | Select-String 'mCurrentFocus'
& $Adb -s emulator-5556 shell dumpsys window | Select-String 'mCurrentFocus'
```

当前窗口的包名包含 `com.bilibili.priconne` 时对应公主连结，包含 `com.miHoYo.HSoDv2` 时对应崩坏学园 2。若没有返回可用的窗口结果，等现有队列结束后，在雷电多开管理器中只打开其中一款游戏的实例并运行 `& $Adb devices -l`，记下序列号，再打开另一个实例。重复安装同一个游戏时，以所用窗口为准。[MaaBH2 渠道包名](https://github.com/freeze-12/MaaBH2/blob/bd2f83a6dbd6dc5516a79e910ced08b745e8eb70/interface.json)

确认两个实例在 `devices -l` 中均为 `device` 后，通过重复指定 `--serial` 一次登记两个实例。如果只登记其中一个，只写该实例的 `--serial`。

```powershell
& .\.venv\Scripts\python.exe -m scripts.automas_keep_emulator register --adb $Adb --serial emulator-5554 --serial emulator-5556
```

刷新 AUTO-MAS，在两款游戏各自的「托管管理 → 控制配置」里选对应的「Daily Clear Hub 保留雷电（…）」，把同一条命令输出的「模拟器实例」整段粘进去。若确认公主连结是 `emulator-5554`，该托管的实例填 `track-devices | emulator-5554`。若确认崩坏学园 2 是 `emulator-5556`，该托管的实例填 `track-devices | emulator-5556`。保存后每款先单独运行一次领奖任务，确认画面对应各自的窗口。

## 找不到指定的 ADB 实例

以下以崩坏学园 2 对应 `emulator-5556` 为例。先保持该实例打开，再查设备列表和目标状态。

```powershell
& $Adb devices -l
& $Adb -s emulator-5556 get-state
```

- 如果显示 `device`，检查托管「模拟器」和「模拟器实例」是否都对应这一序列号。再执行 `& $Adb -s emulator-5556 shell wm size` 验证 Android 命令可用。如果只在托管中失败，从运行历史打开本次日志，搜索「ADB 连接方式」，核对记录的地址和 ADB 路径。托管已保存的 ADB 路径优先于模拟器目录里的 ADB。[AUTO-MAS 的 ADB 路径选择](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/MaaFW/tools/embedded/runner_task.py#L1553-L1597)
- 如果设备缺席或显示 `offline`，打开崩坏学园 2 对应的雷电窗口并等到 Android 桌面。在该实例的「设置 → 其他设置 → ADB 调试」选择「开启本地连接」，如改过设置则保存并重启该实例。再次查看设备列表；若序列号变了，登记当前序列号并更新该托管的绑定。其他实例可以继续保持打开。[雷电 ADB 本地连接设置](https://www.ldplayer.net/blog/introduction-to-version-4.0.37-and-3.102-features.html)

如果目标雷电窗口已开、已启用 ADB 本地连接，但 `emulator-5556` 依旧缺席或离线，可以登记目标实例的本机 ADB 地址。用 `ldconsole.exe list2` 按窗口标题确认雷电实例编号。雷电默认本机端口为 `5555 + 实例编号 × 2`，例如确认崩坏学园 2 是编号 `1` 时用 `127.0.0.1:5557`。登记脚本会对你指定的本机地址尝试 `adb connect`。原来的 `emulator-5556` 若显示为 `device`，可以继续用原序列号。[雷电实例编号与 ADB 端口](https://jp.ldplayer.net/support/ldconsole-command-line-guide.html)

```powershell
& (Join-Path (Split-Path -Parent $Adb) 'ldconsole.exe') list2
& .\.venv\Scripts\python.exe -m scripts.automas_keep_emulator register --adb $Adb --serial 127.0.0.1:5557
& $Adb -s 127.0.0.1:5557 get-state
& $Adb -s 127.0.0.1:5557 shell pm path com.miHoYo.HSoDv2BiliBiliRelease
```

包名命令以崩坏学园 2 B 服为例。其他渠道请替换成游戏实际包名。确认返回 `device` 和 `package:` 路径，再把对应托管的两项改成新输出的「模拟器」和「模拟器实例」，例如 `track-devices | 127.0.0.1:5557`。运行时 AUTO-MAS 会尝试连接这个地址，公主连结继续使用自己原有的绑定。[AUTO-MAS 的 ADB 重连](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/MaaFW/tools/core/runner/runner.py#L2616-L2688)

## 查看普通 ADB 截图和恢复原绑定

通用连接使用普通 ADB 截图，不使用雷电专用的截图方式。部分雷电游戏的画面可能是黑屏或缺少渲染层。遇到已进游戏但识别始终超时的情况，在游戏主页保持可见并用以下命令查看实际截图。有多开实例时加入登记时所用的 `--serial`。[AUTO-MAS 截图方式实现与雷电渲染说明](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/MaaFW/tools/embedded/runner_task.py#L1862-L1886)

```powershell
$Image = & .\.venv\Scripts\python.exe -m scripts.automas_keep_emulator screenshot --adb $Adb
if ($LASTEXITCODE -eq 0) { Invoke-Item -LiteralPath $Image }
```

截图显示异常，或想让 AUTO-MAS 自动启动和关闭雷电时，把游戏「控制配置」中的「模拟器」和「模拟器实例」换回原先的原生雷电设备。已有「模拟器 2.0」或雷电配置仍可直接选用。所有相关托管都换回原设备后，可以在「模拟器管理」中删除「保留雷电」条目。
