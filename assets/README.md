# 内置日常模板

每个游戏单独使用一份 COCO 标注和对应截图。默认路径为 `assets/local/<游戏 ID>/coco_annotations.json`。本机配置的 `games.<游戏 ID>.templates` 可以改路径。 `assets/local/` 不进入 Git。

以终末地为例，在仓库根目录运行以下 PowerShell 命令。换游戏时将命令中的 ID 替换为 `plan` 输出中的 ID。

```powershell
$Game = 'endfield'
& .\.venv\Scripts\python.exe .\main.py plan --features $Game
& .\.venv\Scripts\python.exe .\main.py gui $Game --debug
```

1. 按本机配置的尺寸运行游戏。用诊断界面验证游戏画面。在「模板」页截图并打开「标注」。标记完成后关闭诊断窗口，标注会自动保存。保留完整截图，匹配会使用标注框在原图里的位置。
2. 每个特征使用 `plan --features` 列出的确切名称，同一名称只保留一份标注。也可使用能导出 COCO 目标检测格式的工具。JSON 保存为 UTF-8 无 BOM，`images[].file_name` 使用相对路径，尺寸和框坐标要与原图一致。
3. 从对应游戏的 `games/<游戏 ID>/flow.py` 按图确认起点和每层页面。入口框应覆盖可以点击的按钮，目的页的标记应选该页独有的稳定元素。返回框需校准实际返回按钮，连续多层页面须能命中相同的返回元素。
4. 为 `*_claim` 选取免费且可领的按钮，避免购入、升级或付费解锁。在同一页暂无奖励时，为 `*_empty` 选取明确的禁用、已领完或空列表状态。常驻标题不能代表领完。领奖可能出现弹窗时，标注实际可关闭的按钮，确保它能和通用确认框区分。
5. 先配置一个步骤，检查有奖励时的领取反馈和返回。再执行一次，确认确实显示无奖励。缺入口、页面失配、领取后无反馈或返回失败均应报告失败。

```powershell
$Staging = ".\configs\$Game\diagnostics\ok_templates"
$Target = ".\assets\local\$Game"
New-Item -ItemType Directory -Force $Target | Out-Null
Copy-Item "$Staging\*" $Target -Recurse -Force
& .\.venv\Scripts\python.exe .\main.py check $Game
& .\.venv\Scripts\python.exe .\main.py run $Game
```

星铁内置邮件以已打开的触屏布局手机菜单为起点，绝区零内置邮件要求先打开游戏菜单。原神与终末地有依赖默认快捷键的步骤。相同游戏换语言、区服或改窗口尺寸后要重新验证模板。
