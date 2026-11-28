# Daily Clear Hub

在 Windows 上用 AUTO-MAS 的同一个队列运行多款游戏。托管里可以选择上游支持的日常和周常，公主连结国服 B 服复用 pcr-script 的识别素材。

- [Windows 一次安装与运行手册](docs/windows.md)
- [NIKKE 国际服、学园偶像大师和 Dot Abyss 配置](docs/new-mfw-games.md)
- [上游项目更新时间](#上游项目更新时间)与[更新操作](#上游更新后怎么操作)
- [七款游戏的实现评估与源码依据](docs/implementation-review.md)
- [内置流程的模板采集说明](assets/README.md)

## 首次准备和运行

在 Windows 上按手册准备 Git 和 Python 3.12。在仓库根目录运行：

```powershell
& .\scripts\setup-windows.ps1 -Games honkai3,starrail,zzz,genshin,pcr,bhxy2,endfield
```

打开 AUTO-MAS，按 [Windows 手册](docs/windows.md)配置各款游戏的客户端或模拟器和任务。在「调度队列」创建队列并添加托管，然后在「调度中心」选择队列，点击「开始执行」。

加装 NIKKE 国际服、学园偶像大师和 Dot Abyss 时，运行 `& .\scripts\setup-windows.ps1 -Games nikke,gakumas,dotabyss`。NIKKE 的 NKAS 托管会自动注册，日常从账号的「通用配置」打开 NKAS 网页逐项设置。[三款游戏的配置步骤](docs/new-mfw-games.md)

要在上述三款游戏执行前自动切换网易 UU，可在安装命令加 `-WithUu`，再按托管类型启用。[UU 加速配置](docs/new-mfw-games.md#可选的-uu-加速)

已有的手动 YAML 可以继续使用 `run`。使用 [ok-script](https://github.com/ok-oldking/ok-script) 和本机 COCO 模板时，选择 `backend: native`，用 `gui endfield --debug` 打开单游戏诊断。

## 上游项目更新时间

[**打开完整可排序图表**](https://electrovalentbond.github.io/daily-clear-hub/)

完整列表默认按最近一次 Git 提交时间倒序排列。点击表头可切换顺序，或按项目名称排序。下图预览最近更新的 12 个项目。数据使用 UTC，由 GitHub Actions 每 6 小时检查一次。

[![依赖项目最近提交时间预览，按时间倒序排列](https://electrovalentbond.github.io/daily-clear-hub/preview.svg)](https://electrovalentbond.github.io/daily-clear-hub/)

<details>
<summary>调度与游戏上游、安装基线</summary>

右列列出 [Windows 安装脚本](scripts/setup-windows.ps1) 使用的版本或提交。

| 用途 | 上游源码 | 安装脚本基线 |
| --- | --- | --- |
| 统一调度 | [AUTO-MAS](https://github.com/AUTO-MAS-Project/AUTO-MAS) | [`v5.8.0`](https://github.com/AUTO-MAS-Project/AUTO-MAS/releases/tag/v5.8.0) |
| 崩坏 3 | [Maa_bbb](https://github.com/miaojiuqing/Maa_bbb) | [`v1.13.22`](https://github.com/miaojiuqing/Maa_bbb/releases/tag/v1.13.22) |
| 崩坏：星穹铁道 | [三月七小助手](https://github.com/moesnow/March7thAssistant) | [`v2026.11.22`](https://github.com/moesnow/March7thAssistant/releases/tag/v2026.11.22) |
| 崩坏：星穹铁道（可选） | [StarRailAssistant](https://github.com/Shasnow/StarRailAssistant) | 按需单独配置 |
| 绝区零 | [绝区零一条龙](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon) | [`v2.6.1`](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon/releases/tag/v2.6.1) |
| 原神 | [BetterGI](https://github.com/babalae/better-genshin-impact) | [`0.67.0`](https://github.com/babalae/better-genshin-impact/releases/tag/0.67.0) |
| 公主连结 B 服 | [pcr-script](https://github.com/Gibberer/pcr-script) | [`d1eb212`](https://github.com/Gibberer/pcr-script/commit/d1eb2120599a5bc42ce934657f7788e1a8f0bfc3) |
| 崩坏学园 2 | [MaaBH2](https://github.com/freeze-12/MaaBH2) | [`v0.3.6`](https://github.com/freeze-12/MaaBH2/releases/tag/v0.3.6) |
| 崩坏学园 2（可选） | [Honkai2Automation](https://github.com/lolineet/Honkai2Automation) | 按需单独配置 |
| 明日方舟：终末地 | [MaaEnd](https://github.com/MaaEnd/MaaEnd) | [`v3.2.0`](https://github.com/MaaEnd/MaaEnd/releases/tag/v3.2.0) |
| NIKKE 国际服 | [NIKKEAutoScript（NKAS）](https://github.com/megumiss/NIKKEAutoScript) | [`v1.2.0`](https://github.com/megumiss/NIKKEAutoScript/releases/tag/v1.2.0) |
| 学园偶像大师 | [MaaGakumasu](https://github.com/SuperWaterGod/MaaGakumasu) | [`v1.5.4`](https://github.com/SuperWaterGod/MaaGakumasu/releases/tag/v1.5.4) |
| Dot Abyss | [MaaDotAbyss](https://github.com/Azure-Sora/MaaDotAbyss) | [`8ec90d7`](https://github.com/Azure-Sora/MaaDotAbyss/commit/8ec90d7b900b9feaaac35cd78498e928e2e2a067) |

</details>

<details>
<summary>运行框架和 Python 依赖源码</summary>

公主连结与 Dot Abyss 的适配器使用 MaaFramework `5.16.1`。其他 MFW 项目的运行环境由 AUTO-MAS 按项目准备。Hub 本地后端和 UU 前置任务的版本见 [Python 依赖清单](requirements.txt) 和 [UU 依赖清单](scripts/uu-requirements.txt)。PySide6、其 Addons / Essentials 和 Shiboken6 共用源码仓库。

- [MaaFramework](https://github.com/MaaXYZ/MaaFramework)
- [pywinauto](https://github.com/pywinauto/pywinauto)
- [RapidOCR](https://github.com/RapidAI/RapidOCR)
- [ok-script](https://github.com/ok-oldking/ok-script)
- [PyYAML](https://github.com/yaml/pyyaml)
- [adbutils](https://github.com/openatx/adbutils)
- [pynput](https://github.com/moses-palmer/pynput)
- [OnnxOCR PP-OCRv5](https://github.com/ok-oldking/OnnxOCR)
- [OpenVINO](https://github.com/openvinotoolkit/openvino)
- [opencv-python](https://github.com/opencv/opencv-python)
- [OpenCC](https://github.com/BYVoid/OpenCC)
- [PySide6 Fluent Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets/tree/PySide6)
- [requests](https://github.com/psf/requests)
- [urllib3](https://github.com/urllib3/urllib3)
- [certifi](https://github.com/certifi/python-certifi)
- [charset-normalizer](https://github.com/jawah/charset_normalizer)
- [idna](https://github.com/kjd/idna)
- [retry2](https://github.com/eSAMTrade/retry)
- [NumPy](https://github.com/numpy/numpy)
- [Pillow](https://github.com/python-pillow/Pillow)
- [pyclipper](https://github.com/fonttools/pyclipper)
- [Shapely](https://github.com/shapely/shapely)
- [OpenVINO Telemetry](https://github.com/openvinotoolkit/telemetry)
- [darkdetect](https://github.com/albertosottile/darkdetect)
- [PySide6 Frameless Window](https://github.com/zhiyiYo/PyQt-Frameless-Window/tree/PySide6)
- [pywin32](https://github.com/mhammond/pywin32)
- [pycaw](https://github.com/AndreMiras/pycaw)
- [comtypes](https://github.com/enthought/comtypes)
- [psutil](https://github.com/giampaolo/psutil)
- [mouse](https://github.com/boppreh/mouse)
- [PyDirectInput](https://github.com/learncodebygaming/pydirectinput)
- [decorator](https://github.com/micheles/decorator)
- [deprecation](https://github.com/briancurtin/deprecation)
- [packaging](https://github.com/pypa/packaging)
- [six](https://github.com/benjaminp/six)
- [typing-extensions](https://github.com/python/typing_extensions)
- [PyAppify Python](https://github.com/ok-oldking/pyappify-python)
- [Brotli](https://github.com/google/brotli)
- [tqdm](https://github.com/tqdm/tqdm)
- [Playwright for Python](https://github.com/microsoft/playwright-python)
- [UnityPy](https://github.com/K0lb3/UnityPy)
- [PySide6 / Shiboken6](https://github.com/qtproject/pyside-pyside-setup)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [ONNX Runtime](https://onnxruntime.ai/) · [官方 GitHub 仓库](https://github.com/microsoft/onnxruntime) · [PyPI 发行记录](https://pypi.org/project/onnxruntime/#history)

</details>

<details>
<summary>安装工具和 CI 依赖源码</summary>

- [PyAppify](https://github.com/ok-oldking/pyappify)
- [PyAppify Action](https://github.com/ok-oldking/pyappify-action)
- [partial-sync-repo](https://github.com/ok-oldking/partial-sync-repo)
- [actions/checkout](https://github.com/actions/checkout)
- [actions/upload-pages-artifact](https://github.com/actions/upload-pages-artifact)
- [actions/deploy-pages](https://github.com/actions/deploy-pages)
- [actions/setup-python](https://github.com/actions/setup-python)
- [action-gh-release](https://github.com/softprops/action-gh-release)
- [Mirror 酱上传 Action](https://github.com/MirrorChyan/uploading-action)
- [Mirror 酱发布说明 Action](https://github.com/MirrorChyan/release-note-action)
- [Git for Windows](https://github.com/git-for-windows/git)
- [CPython](https://github.com/python/cpython)
- [WinGet](https://github.com/microsoft/winget-cli)
- [curl](https://github.com/curl/curl)
- [uv](https://github.com/astral-sh/uv)
- [Android ADB](https://android.googlesource.com/platform/packages/modules/adb/)

</details>

## 上游更新后怎么操作

Git 提交只表示上游源码有变化。日常运行正常时，可以继续用当前版本。在 AUTO-MAS v5.8.0 的「设置 → 关于 → 更新配置」，可以开启「启动时尝试更新后端」，也可以手动点「检查更新」。同一版本分支的后端补丁准备好后，重启应用即可生效。AUTO-MAS 本体跨版本更新通过应用的更新提示或新版安装包完成。[AUTO-MAS 更新说明](https://doc.auto-mas.top/docs/user-guide#第一次启动) · [v5.8.0 更新界面](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/frontend/src/views/setting/UpdateSettingsSection.vue#L78-L95)

- **原版 MFW 托管**（例如崩坏 3 的 Maa_bbb、以「MFW 脚本」导入的终末地 MaaEnd）。在托管的「项目更新」选好更新源和通道，将「自动更新」设为「运行前」。执行该托管时，AUTO-MAS 会检查上游发布包并更新自己的副本。也可以在托管空闲时手动检查并更新。终末地若用的是「MaaEnd脚本」专项托管，则在「MaaEnd 程序更新」开启「接管更新」。[MFW 项目更新](https://doc.auto-mas.top/docs/script-guide/maafw.html#项目更新) · [MaaEnd 专项更新设置](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/models/config/script.py#L1278-L1289)
- **三月七、绝区零一条龙、BetterGI**。三月七和已选用的 SRA 按星铁托管的更新设置在运行前检查。绝区零使用一条龙集成启动器时，由它按「自动更新代码」设置更新。如果新版要求升级启动器或运行环境，按一条龙的发布说明操作。BetterGI 可以在自身界面更新，或在 AUTO-MAS 的「BetterGI 程序更新」开启「接管更新」。[星铁更新逻辑](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/app/task/HSR/manager.py#L375-L429) · [绝区零一条龙启动器](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon/blob/v2.6.1/docs/develop/one_dragon/runtime_launcher.md#L118-L143) · [BetterGI 更新设置](https://github.com/AUTO-MAS-Project/AUTO-MAS/blob/v5.8.0/frontend/src/views/EditView/Script/components/BetterGIProgramUpdateSettings.vue#L17-L49)
- **Hub 适配或补丁版**（公主连结、崩坏学园 2、NIKKE、学园偶像大师和 Dot Abyss，含 UU 版）。这些流程使用 Hub 准备的本机文件。上游有新版时，只有需要采用新版本或游戏改版导致流程失效，才需要调整 Hub 的安装版本、校验值或适配代码。等 Hub 发布对应更新后，先停止托管，再拉取并重跑对应游戏的安装命令。已经启用的 `-WithUu` 和自定义 `-ToolsRoot` 沿用原值。

  ```powershell
  git pull --ff-only
  & .\scripts\setup-windows.ps1 -Games gakumas -WithUu
  ```

  对 MFW 托管，启用「基本信息 → 跟随来源目录」并点「立即同步」，让 AUTO-MAS 使用 Hub 准备的版本和补丁。若新版本换了安装目录，按该次更新说明检查托管的来源路径。NIKKE 走通用托管，安装脚本会更新本机适配器和注册配置。公主连结当前固定到指定提交，并复用已有 `pcr-script` 目录，换上游提交时按该次迁移说明处理。Python 库按 Hub 的依赖清单安装。[来源目录同步](https://doc.auto-mas.top/docs/script-guide/maafw.html#项目更新) · [Windows 安装脚本](scripts/setup-windows.ps1)

## 开发验证

```bash
python3 -m venv .venv
.venv/bin/python -m pip install pyyaml
./run_tests.sh
```
