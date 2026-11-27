# Daily Clear Hub

在 Windows 上用 AUTO-MAS 的同一个队列运行多款游戏。托管里可以选择上游支持的日常和周常，公主连结国服 B 服复用 pcr-script 的识别素材。

- [Windows 一次安装与运行手册](docs/windows.md)
- [NIKKE 国际服、学园偶像大师和 Dot Abyss 配置](docs/new-mfw-games.md)
- [七款游戏的实现评估与源码依据](docs/implementation-review.md)
- [内置流程的模板采集说明](assets/README.md)

## 首次准备和运行

在 Windows 上按手册准备 Git 和 Python 3.12。在仓库根目录运行：

```powershell
& .\scripts\setup-windows.ps1 -Games honkai3,starrail,zzz,genshin,pcr,bhxy2,endfield
```

打开 AUTO-MAS，按 [Windows 手册](docs/windows.md)配置各款游戏的客户端或模拟器和任务。在「调度队列」创建队列并添加托管，然后在「调度中心」选择队列，点击「开始执行」。

加装 NIKKE 国际服、学园偶像大师和 Dot Abyss 时，运行 `& .\scripts\setup-windows.ps1 -Games nikke,gakumas,dotabyss`，再将新托管加入已有队列。[三款游戏的配置步骤](docs/new-mfw-games.md)

要在上述三款游戏执行前自动切换网易 UU，可在安装命令加 `-WithUu`，然后在托管中勾选「切换网易 UU 加速」。[UU 加速配置](docs/new-mfw-games.md#可选的-uu-加速)

已有的手动 YAML 可以继续使用 `run`。使用 [ok-script](https://github.com/ok-oldking/ok-script) 和本机 COCO 模板时，选择 `backend: native`，用 `gui endfield --debug` 打开单游戏诊断。

## 开源项目与源码仓库

### 调度与游戏上游

- 统一调度和账号托管使用 [AUTO-MAS](https://github.com/AUTO-MAS-Project/AUTO-MAS)。
- 崩坏 3 使用 [Maa_bbb](https://github.com/miaojiuqing/Maa_bbb)。
- 崩坏：星穹铁道使用 [三月七小助手（March7thAssistant）](https://github.com/moesnow/March7thAssistant)。AUTO-MAS 的星铁托管还可选配 [StarRailAssistant（SRA）](https://github.com/Shasnow/StarRailAssistant)。
- 绝区零使用 [绝区零一条龙（ZenlessZoneZero-OneDragon）](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon)。
- 原神使用 [更好的原神（BetterGI）](https://github.com/babalae/better-genshin-impact)。
- 公主连结 B 服使用 [pcr-script](https://github.com/Gibberer/pcr-script) 的任务与识别素材，由 Hub 的 MFW 适配器接入 AUTO-MAS。
- 崩坏学园 2 使用 [MaaBH2](https://github.com/freeze-12/MaaBH2)，也可手动配置独立的 [Honkai2Automation](https://github.com/lolineet/Honkai2Automation) 后端。
- 明日方舟：终末地使用 [MaaEnd](https://github.com/MaaEnd/MaaEnd)。
- NIKKE 国际服使用 [MDA](https://github.com/1204244136/MDA) 的简中识别资源。
- 学园偶像大师使用 [MaaGakumasu](https://github.com/SuperWaterGod/MaaGakumasu)。
- Dot Abyss 使用 [MaaDotAbyss](https://github.com/Azure-Sora/MaaDotAbyss) 的日文 DMM 流程，由 Hub 的 MFW 适配器接入 AUTO-MAS。

### 运行框架和依赖

- MFW 项目和公主连结的 Agent 使用 [MaaFramework](https://github.com/MaaXYZ/MaaFramework)。
- 网易 UU 的可选前置任务使用 [pywinauto](https://github.com/pywinauto/pywinauto) 与 [RapidOCR](https://github.com/RapidAI/RapidOCR) 读取 Windows 客户端界面。
- Hub 的本地模板后端使用 [ok-script](https://github.com/ok-oldking/ok-script)。
- 配置、设备与输入依赖包括 [PyYAML](https://github.com/yaml/pyyaml)、[adbutils](https://github.com/openatx/adbutils) 和 [pynput](https://github.com/moses-palmer/pynput)。
- OCR 和图像处理使用 [OnnxOCR PP-OCRv5](https://github.com/ok-oldking/OnnxOCR)、[OpenVINO](https://github.com/openvinotoolkit/openvino)、[opencv-python](https://github.com/opencv/opencv-python) 和 [OpenCC](https://github.com/BYVoid/OpenCC)。
- 本地界面使用 [PySide6](https://code.qt.io/cgit/pyside/pyside-setup.git/) 和 [PySide6 Fluent Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets/tree/PySide6)。

<details>
<summary>其余 Python 依赖、安装工具与 CI</summary>

[Python 版本清单](requirements.txt)中还锁定了以下依赖。

- 网络与编码包括 [requests](https://github.com/psf/requests)、[urllib3](https://github.com/urllib3/urllib3)、[certifi](https://github.com/certifi/python-certifi)、[charset-normalizer](https://github.com/jawah/charset_normalizer)、[idna](https://github.com/kjd/idna) 和 [retry2](https://github.com/eSAMTrade/retry)。
- 图像、几何和推理包括 [NumPy](https://github.com/numpy/numpy)、[Pillow](https://github.com/python-pillow/Pillow)、[pyclipper](https://github.com/fonttools/pyclipper)、[Shapely](https://github.com/shapely/shapely) 和 [OpenVINO Telemetry](https://github.com/openvinotoolkit/telemetry)。
- Windows 界面和输入包括 [darkdetect](https://github.com/albertosottile/darkdetect)、[PySide6 Frameless Window](https://github.com/zhiyiYo/PyQt-Frameless-Window/tree/PySide6)、[pywin32](https://github.com/mhammond/pywin32)、[pycaw](https://github.com/AndreMiras/pycaw)、[comtypes](https://github.com/enthought/comtypes)、[psutil](https://github.com/giampaolo/psutil)、[mouse](https://github.com/boppreh/mouse) 和 [PyDirectInput](https://github.com/learncodebygaming/pydirectinput)。`pyside6-addons`、`pyside6-essentials` 和 `shiboken6` 与 [PySide6](https://code.qt.io/cgit/pyside/pyside-setup.git/) 共用源码仓库。
- Python 工具库包括 [decorator](https://github.com/micheles/decorator)、[deprecation](https://github.com/briancurtin/deprecation)、[packaging](https://github.com/pypa/packaging)、[six](https://github.com/benjaminp/six) 和 [typing-extensions](https://github.com/python/typing_extensions)。
- Python 打包与更新接口由 [PyAppify Python](https://github.com/ok-oldking/pyappify-python) 提供。

Windows 安装脚本为 pcr-script 创建单独的环境，还会按上游清单安装 [Brotli](https://github.com/google/brotli)、[tqdm](https://github.com/tqdm/tqdm)、[RapidOCR](https://github.com/RapidAI/RapidOCR)、[Playwright for Python](https://github.com/microsoft/playwright-python)、[UnityPy](https://github.com/K0lb3/UnityPy) 和 ONNX Runtime。[ONNX Runtime 官方 Git 仓库](https://github.com/microsoft/onnxruntime)目前返回 404，发行包可在 [PyPI](https://pypi.org/project/onnxruntime/) 查看。

- CI 配置引用 [PyAppify](https://github.com/ok-oldking/pyappify)、[PyAppify Action](https://github.com/ok-oldking/pyappify-action)、[partial-sync-repo](https://github.com/ok-oldking/partial-sync-repo)、[actions/checkout](https://github.com/actions/checkout)、[actions/setup-python](https://github.com/actions/setup-python)、[action-gh-release](https://github.com/softprops/action-gh-release)、[Mirror 酱上传 Action](https://github.com/MirrorChyan/uploading-action) 和 [Mirror 酱发布说明 Action](https://github.com/MirrorChyan/release-note-action)。
- 安装、设备连接和开发工具包括 [Git for Windows](https://github.com/git-for-windows/git)、[CPython](https://github.com/python/cpython)、[WinGet](https://github.com/microsoft/winget-cli)、[curl](https://github.com/curl/curl)、[Android ADB](https://android.googlesource.com/platform/packages/modules/adb/) 和 [uv](https://github.com/astral-sh/uv)。

</details>

## 开发验证

```bash
python3 -m venv .venv
.venv/bin/python -m pip install pyyaml
./run_tests.sh
```
