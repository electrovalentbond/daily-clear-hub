# Daily Clear Hub

在 Windows 上按一份配置运行七款游戏的日常。内置流程使用 [ok-script](https://github.com/ok-oldking/ok-script) 识别画面和发送输入，并报告已领完、确认无奖励或失败。星铁可选三月七小助手，崩坏学园 2 可选 HKA，由 Hub 等待并检查各自的运行结果。

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

仓库默认关闭所有游戏。内置路线用于免费奖励领取，需要按你的游戏版本和语言采集 COCO 截图模板，再在 Windows 验证起点、领奖、领完和返回。星铁和崩坏学园 2 的外部后端使用各自的配置与识别资源。两种模式都可加入同一队列。

## 开发验证

```bash
python3 -m venv .venv
.venv/bin/python -m pip install pyyaml
./run_tests.sh
```
