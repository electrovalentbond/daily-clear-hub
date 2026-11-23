# Daily Clear Hub

在 Windows 上用 AUTO-MAS 的同一个队列运行七款游戏。托管里可以选择上游支持的日常和周常，公主连结国服 B 服复用 pcr-script 的识别素材。

- [Windows 一次安装与运行手册](docs/windows.md)
- [七款游戏的实现评估与源码依据](docs/implementation-review.md)
- [内置流程的模板采集说明](assets/README.md)

## 首次准备和运行

在 Windows 上按手册准备 Git 和 Python 3.12。在仓库根目录运行：

```powershell
& .\scripts\setup-windows.ps1 -Games honkai3,starrail,zzz,genshin,pcr,bhxy2,endfield
```

打开 AUTO-MAS，按 [Windows 手册](docs/windows.md)配置各款游戏的客户端或模拟器和任务。在「调度队列」创建队列并添加托管，然后在「调度中心」选择队列，点击「开始执行」。

已有的手动 YAML 可以继续使用 `run`。使用 [ok-script](https://github.com/ok-oldking/ok-script) 和本机 COCO 模板时，选择 `backend: native`，用 `gui endfield --debug` 打开单游戏诊断。

## 开发验证

```bash
python3 -m venv .venv
.venv/bin/python -m pip install pyyaml
./run_tests.sh
```
