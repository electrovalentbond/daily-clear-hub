# Daily Clear Hub

在 Windows 上按一份配置运行七款游戏的日常。上游后端使用各项目自带的素材。崩坏 3、终末地、原神和绝区零通过 AUTO-MAS 运行。公主连结国服 B 服使用 pcr-script，星铁使用三月七小助手，崩坏学园 2 使用 HKA。Hub 等待各游戏的运行报告，再继续队列。

- [Windows 安装与运行手册](docs/windows.md)
- [七款游戏的实现评估与源码依据](docs/implementation-review.md)
- [内置流程的模板采集说明](assets/README.md)

## 入口

在仓库根目录按 Windows 手册创建 `.venv`，复制 `config.local.yaml.example` 为 `config.local.yaml` 并设置运行目标。

```powershell
& .\.venv\Scripts\python.exe .\main.py plan
& .\.venv\Scripts\python.exe .\main.py check
& .\.venv\Scripts\python.exe .\main.py run
```

`plan` 列出全部游戏和步骤。 `check` 检查配置和素材，`run` 按 `schedule_order` 运行已启用的游戏。可在命令后传入一个或多个游戏 ID 单独联调，例如 `run endfield`。`gui endfield --debug` 打开单游戏的 ok-script 截图诊断工具。

仓库默认关闭所有游戏。配置示例选择免标注的上游后端，按手册安装与配置后逐款检查，再将通过的游戏加入队列。也可选择 `backend: native`，使用 [ok-script](https://github.com/ok-oldking/ok-script) 和本机 COCO 截图模板处理免费领奖。

## 开发验证

```bash
python3 -m venv .venv
.venv/bin/python -m pip install pyyaml
./run_tests.sh
```
