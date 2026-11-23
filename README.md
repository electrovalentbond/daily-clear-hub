# Daily Clear Hub

在 Windows 上从一个队列运行七款游戏的日常。六款游戏可以在 AUTO-MAS 中集中设置，Hub 自动读取托管。公主连结国服 B 服由同一个命令识别并使用 pcr-script。上游后端使用自带的识别素材。

- [Windows 一次安装与运行手册](docs/windows.md)
- [七款游戏的实现评估与源码依据](docs/implementation-review.md)
- [内置流程的模板采集说明](assets/README.md)

## 首次准备和运行

在 Windows 上按手册准备 Git 和 Python 3.12。在仓库根目录运行：

```powershell
& .\scripts\setup-windows.ps1 -Games honkai3,starrail,zzz,genshin,pcr,bhxy2,endfield
```

打开 AUTO-MAS，配置要运行的托管。公主连结使用已登录的 B 服 ADB 设备。首次检查可以在命令末尾指定游戏 ID。

```powershell
& .\.venv\Scripts\python.exe .\main.py plan --automas
& .\.venv\Scripts\python.exe .\main.py check --automas
& .\.venv\Scripts\python.exe .\main.py run --automas
```

已有的手动 YAML 可以继续使用 `run`。使用 [ok-script](https://github.com/ok-oldking/ok-script) 和本机 COCO 模板时，选择 `backend: native`，用 `gui endfield --debug` 打开单游戏诊断。

## 开发验证

```bash
python3 -m venv .venv
.venv/bin/python -m pip install pyyaml
./run_tests.sh
```
