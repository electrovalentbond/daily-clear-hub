# AUTO-MAS 日常结束后保留雷电模拟器

AUTO-MAS v5.8.0 的原生雷电和「模拟器 2.0」绑定会在 MFW 托管结束时关闭模拟器。若想保留窗口，可以新增一个「通用」模拟器连接已打开的实例。此配置让 AUTO-MAS 管理 ADB 的设备监视进程，日常完成、失败、停止或重试时只会清理该监视进程。雷电由你手动启动，可以在日常结束后继续操作。[AUTO-MAS 的 ADB 生命周期说明](https://doc.auto-mas.top/developer/maafw/tradeoffs.html) · [通用模拟器实现](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/utils/common/emulator/general.py) · [Android ADB 命令](https://android.googlesource.com/platform/packages/modules/adb/+/refs/tags/android-vts-17.0_r1/docs/user/adb.1.md)

## 添加保留模式

1. 按 Windows 手册完成环境和托管配置。手动打开目标雷电实例，等待进入 Android 桌面，在该实例的「设置 → 其他设置 → ADB 调试」选择「开启本地连接」。改过设置时保存并重启这个实例。保持 AUTO-MAS 运行，等现有队列结束。[Windows 手册](windows.md) · [雷电 ADB 设置](https://www.ldplayer.net/blog/introduction-to-version-4.0.37-and-3.102-features.html)
2. 在 Hub 仓库根目录运行以下命令。将 `$Adb` 改成雷电自带的 `adb.exe` 路径。`list2` 输出每个实例的编号和窗口标题，第一列为编号。确认目标窗口后，把示例中的 `0` 换成实际编号。

   ```powershell
   $Adb = 'C:\LDPlayer\LDPlayer9\adb.exe'
   & (Join-Path (Split-Path -Parent $Adb) 'ldconsole.exe') list2
   & .\.venv\Scripts\python.exe -m scripts.automas_keep_emulator register --adb $Adb --ld-index 0
   ```

   脚本会核对目标已进入 Android，按雷电的默认规则 `5555 + 实例编号 × 2` 计算本机端口，并在 ADB 返回 `device` 后才登记。AUTO-MAS 运行时会主动连接该地址。使用非默认 AUTO-MAS 端口时可加 `--port`。[雷电实例和 ADB 端口](https://jp.ldplayer.net/support/ldconsole-command-line-guide.html) · [AUTO-MAS 的 ADB 重连](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/MaaFW/tools/core/runner/runner.py#L2616-L2688)

3. 刷新 AUTO-MAS，再进入公主连结或崩坏学园 2 的「托管管理 → 控制配置」。「模拟器」选命令输出的「Daily Clear Hub 保留雷电（…）」，把输出的「模拟器实例」整段粘到对应输入框，例如 `track-devices | 127.0.0.1:5555`。点击输入框外保存。两款游戏共用一个实例时，选同一个设备并粘贴同一段实例。[通用实例输入框](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/frontend/src/views/EditView/Script/components/EmulatorInstanceField.vue#L14-L22)

每次运行前先打开雷电。公主连结的日常项目会启动 B 服游戏。崩坏学园 2 可以手动进入游戏主页，也可以在 MaaBH2 队列开头添加「启动游戏」并选自己的渠道。先各跑一次领奖检查配置。[MaaBH2 启动选项](https://github.com/freeze-12/MaaBH2/blob/bd2f83a6dbd6dc5516a79e910ced08b745e8eb70/interface.json)

## 两款游戏分开使用雷电实例

用 `list2` 的编号和窗口标题核对每款游戏所在的实例。打开两个实例后，可重复指定 `--ld-index` 一次登记。以下以 `0` 和 `1` 为例。

```powershell
& .\.venv\Scripts\python.exe -m scripts.automas_keep_emulator register --adb $Adb --ld-index 0 --ld-index 1
```

分别在两款游戏的「控制配置」选择对应的「保留雷电」设备，并粘贴匹配的「模拟器实例」。例如公主连结使用编号 `0` 时填 `track-devices | 127.0.0.1:5555`，崩坏学园 2 使用编号 `1` 时填 `track-devices | 127.0.0.1:5557`。以你的游戏和实例对应关系为准。

## 找不到指定的 ADB 实例

如果旧托管使用 `track-devices | emulator-5554` 或 `track-devices | emulator-5556`，并在「模拟器启动完成」之后报 `device … not found`，这条启动日志只表示 ADB 监视进程已经启动。使用上面的 `--ld-index` 重新登记并选择新的本机地址。下一次运行日志应显示「ADB 网络设备已连接」或「ADB 设备已就绪」。[通用模拟器的启动逻辑](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/utils/common/emulator/general.py#L61-L90) · [MaaFW 就绪检查](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/MaaFW/tools/core/runner/runner.py#L2616-L2688)

如果默认端口连不上，可以先用原生雷电选择器跑一次，查看成功日志「ADB 连接方式」中的 `地址=` 和 `ADB 路径=`。若原生使用不同的本机端口，手动重开雷电后，按日志里的实际地址登记。以下以 `127.0.0.1:5557` 为例。[原生雷电如何选择地址](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/utils/common/emulator/ldplayer.py#L326-L340)

```powershell
& .\.venv\Scripts\python.exe -m scripts.automas_keep_emulator register --adb $Adb --serial 127.0.0.1:5557
```

如果仍连不上，原生雷电选择器可以继续使用。若崩坏学园 2 同时提示「项目里识别到多个游戏包名」，这条提示针对客户端渠道选择。保留模式下请手动进入游戏，或给 MaaBH2 的「启动游戏」任务选对应渠道。

## 查看普通 ADB 截图和恢复原绑定

通用连接使用普通 ADB 截图。部分雷电游戏的画面可能是黑屏或缺少渲染层。遇到已进游戏但识别始终超时的情况，在游戏主页保持可见，用登记时输出的本机地址查看实际截图。[AUTO-MAS 截图方式实现与雷电渲染说明](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/MaaFW/tools/embedded/runner_task.py#L1862-L1886)

```powershell
$Image = & .\.venv\Scripts\python.exe -m scripts.automas_keep_emulator screenshot --adb $Adb --serial 127.0.0.1:5555
if ($LASTEXITCODE -eq 0) { Invoke-Item -LiteralPath $Image }
```

截图显示异常，或想让 AUTO-MAS 自动启动和关闭雷电时，把游戏「控制配置」中的「模拟器」和「模拟器实例」换回原先的原生雷电设备。已有「模拟器 2.0」或雷电配置仍可直接选用。所有相关托管都换回原设备后，可以在「模拟器管理」中删除「保留雷电」条目。
