# AUTO-MAS 日常结束后保留雷电模拟器

AUTO-MAS v5.8.0 的原生雷电和「模拟器 2.0」绑定会在 MFW 托管结束时关闭模拟器。若想保留窗口，可以新增一个「通用」模拟器连接已打开的实例。此配置让 AUTO-MAS 管理 ADB 的设备监视进程，日常完成、失败、停止或重试时只会清理该监视进程。雷电由你手动启动，可以在日常结束后继续操作。[AUTO-MAS 的 ADB 生命周期说明](https://doc.auto-mas.top/developer/maafw/tradeoffs.html) · [通用模拟器实现](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/utils/common/emulator/general.py) · [Android ADB 命令](https://android.googlesource.com/platform/packages/modules/adb/+/refs/tags/android-vts-17.0_r1/docs/user/adb.1.md)

## 添加保留模式

1. 按 [Windows 手册](windows.md) 完成环境和托管配置。手动打开雷电对应的多开实例，等待进入 Android 桌面，在模拟器设置启用 ADB 本地连接。保持 AUTO-MAS 运行，等现有队列结束。
2. 在 Hub 仓库根目录运行以下命令。将 `$Adb` 改成实际雷电安装目录下的 `adb.exe` 路径。

   ```powershell
   $Adb = 'C:\LDPlayer\LDPlayer9\adb.exe'
   & .\.venv\Scripts\python.exe -m scripts.automas_keep_emulator register --adb $Adb
   ```

   如果提示发现多个本地模拟器，可以只打开目标实例，也可以按设备列表指定序列号。非默认本机 AUTO-MAS 端口用 `--port` 指定。

   ```powershell
   & $Adb devices -l
   & .\.venv\Scripts\python.exe -m scripts.automas_keep_emulator register --adb $Adb --serial emulator-5554
   ```

3. 刷新 AUTO-MAS，再进入公主连结或崩坏学园 2 的「托管管理 → 控制配置」。「模拟器」选命令输出的「Daily Clear Hub 保留雷电（…）」，把它输出的「模拟器实例」整段粘到对应输入框，例如 `track-devices | emulator-5554`。点击输入框外保存。两款游戏共用一个已登录的雷电实例时，可选同一个设备并粘贴同一段实例。新增设备也会出现在原有「模拟器 2.0」配置所在的模拟器列表中。[模拟器类型选择](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/frontend/src/views/Emulator.vue#L60-L69) · [通用实例输入框](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/frontend/src/views/EditView/Script/components/EmulatorInstanceField.vue#L14-L22)

每次运行前确认雷电已经打开。公主连结的日常项目会启动 B 服游戏。崩坏学园 2 保留模式下可以先手动进入游戏主页，也可以在 MaaBH2 队列中添加「启动游戏」并选正确渠道。先各跑一次低风险任务，例如领奖，两款游戏共用实例时按队列顺序运行。

## 查看普通 ADB 截图和恢复原绑定

通用连接使用普通 ADB 截图，不使用雷电专用的截图方式。部分雷电游戏的画面可能是黑屏或缺少渲染层。遇到已进游戏但识别始终超时的情况，在游戏主页保持可见并用以下命令查看实际截图。有多开实例时加入登记时所用的 `--serial`。[AUTO-MAS 截图方式实现与雷电渲染说明](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/MaaFW/tools/embedded/runner_task.py#L1862-L1886)

```powershell
$Image = & .\.venv\Scripts\python.exe -m scripts.automas_keep_emulator screenshot --adb $Adb
if ($LASTEXITCODE -eq 0) { Invoke-Item -LiteralPath $Image }
```

截图显示异常，或想让 AUTO-MAS 自动启动和关闭雷电时，把游戏「控制配置」中的「模拟器」和「模拟器实例」换回原先的原生雷电设备。已有「模拟器 2.0」或雷电配置仍可直接选用。所有相关托管都换回原设备后，可以在「模拟器管理」中删除「保留雷电」条目。
