# 崩坏学园 2 的 MaaBH2 托管

MaaBH2 可在 AUTO-MAS 中作为 MFW 项目运行。官方发布包包含流程、识别图片和 OCR 模型。可以复用已经登录的雷电 9 实例，分辨率设为 1280×720 横屏。上游已实测 UC 服和混服。B 服、官服、腾讯服和测试服有启动选项，首次可在游戏中确认领奖结果。[MaaBH2 支持渠道](https://github.com/freeze-12/MaaBH2/blob/bd2f83a6dbd6dc5516a79e910ced08b745e8eb70/README.md#支持渠道) · [MaaBH2 v0.3.6 发布包](https://github.com/freeze-12/MaaBH2/releases/tag/v0.3.6)

## 导入项目

已通过 Hub 下载官方发布包时，使用解压后的 MaaBH2 项目目录。也可单独下载固定版本。

```powershell
$MaaBh2Zip = Join-Path $env:TEMP 'MaaBH2-v0.3.6-win-x64.zip'
$MaaBh2Root = Join-Path $env:USERPROFILE 'Games\DailyAutomation\MaaBH2-v0.3.6'
$MaaBh2Url = 'https://github.com/freeze-12/MaaBH2/releases/download/v0.3.6/MaaBH2-v0.3.6-win-x64.zip'
if (-not (Test-Path (Join-Path $MaaBh2Root 'interface.json'))) {
    Invoke-WebRequest -Uri $MaaBh2Url -OutFile $MaaBh2Zip
    if ((Get-FileHash -LiteralPath $MaaBh2Zip -Algorithm SHA256).Hash -ne '64e97957ea448b0b9505b2882e33c4e63b9a537d91c2d3c4d42154941c867f2e') {
        throw 'MaaBH2 压缩包 SHA-256 校验失败。'
    }
    Expand-Archive -LiteralPath $MaaBh2Zip -DestinationPath $MaaBh2Root
}
$MaaBh2Root
```

1. 在 AUTO-MAS「托管管理」新建「MFW 项目」，选择命令输出的目录，控制器选「雷电模拟器」，资源选「默认」。
2. 绑定已经登录游戏的实例。若用 B 服，明确填写游戏包名 `com.miHoYo.HSoDv2BiliBiliRelease`。选择其他渠道时填写其包名。AUTO-MAS 已负责启动正确游戏时，可以在 MaaBH2 队列里省去「启动游戏」；这个上游任务在初次启动失败后会轮询其他渠道。
3. 添加或启用一个账号。首次可让游戏停在主页，任务队列只选「10. 每日每周任务奖励领取」。上线检查确认后，再加入社团、使魔探险和清体力。加入清体力前，按任务说明设置装备及摇杆。预设也包含购买和装备切换，请按需要选择任务。[MaaBH2 任务和启动选项](https://github.com/freeze-12/MaaBH2/blob/bd2f83a6dbd6dc5516a79e910ced08b745e8eb70/interface.json) · [AUTO-MAS MFW 配置方法](https://doc.auto-mas.top/docs/script-guide/maafw.html)

完成托管后，回到 Hub 仓库执行检查及单款日常。

```powershell
& .\.venv\Scripts\python.exe .\main.py check --automas bhxy2
& .\.venv\Scripts\python.exe .\main.py run --automas bhxy2
```
