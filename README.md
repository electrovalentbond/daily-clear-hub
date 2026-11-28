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

时间徽章读取上游 Git 默认分支最近一次提交的提交者时间，使用 UTC。两个 PySide6 界面组件读取各自的 `PySide6` 分支，Qt 使用其官方 GitHub 镜像。徽章有缓存，点击可查看提交记录。右列是 [Windows 安装脚本](scripts/setup-windows.ps1) 使用的版本或提交。

| 用途 | 上游源码 | Git 最新提交（UTC） | 安装脚本基线 |
| --- | --- | --- | --- |
| 统一调度 | [AUTO-MAS](https://github.com/AUTO-MAS-Project/AUTO-MAS) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2FAUTO-MAS-Project%2FAUTO-MAS%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/AUTO-MAS-Project/AUTO-MAS/commits) | [`v5.8.0`](https://github.com/AUTO-MAS-Project/AUTO-MAS/releases/tag/v5.8.0) |
| 崩坏 3 | [Maa_bbb](https://github.com/miaojiuqing/Maa_bbb) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fmiaojiuqing%2FMaa_bbb%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/miaojiuqing/Maa_bbb/commits) | [`v1.13.22`](https://github.com/miaojiuqing/Maa_bbb/releases/tag/v1.13.22) |
| 崩坏：星穹铁道 | [三月七小助手](https://github.com/moesnow/March7thAssistant) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fmoesnow%2FMarch7thAssistant%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/moesnow/March7thAssistant/commits) | [`v2026.11.22`](https://github.com/moesnow/March7thAssistant/releases/tag/v2026.11.22) |
| 崩坏：星穹铁道（可选） | [StarRailAssistant](https://github.com/Shasnow/StarRailAssistant) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2FShasnow%2FStarRailAssistant%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/Shasnow/StarRailAssistant/commits) | 按需单独配置 |
| 绝区零 | [绝区零一条龙](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2FOneDragon-Anything%2FZenlessZoneZero-OneDragon%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon/commits) | [`v2.6.1`](https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon/releases/tag/v2.6.1) |
| 原神 | [BetterGI](https://github.com/babalae/better-genshin-impact) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fbabalae%2Fbetter-genshin-impact%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/babalae/better-genshin-impact/commits) | [`0.67.0`](https://github.com/babalae/better-genshin-impact/releases/tag/0.67.0) |
| 公主连结 B 服 | [pcr-script](https://github.com/Gibberer/pcr-script) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2FGibberer%2Fpcr-script%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/Gibberer/pcr-script/commits) | [`d1eb212`](https://github.com/Gibberer/pcr-script/commit/d1eb2120599a5bc42ce934657f7788e1a8f0bfc3) |
| 崩坏学园 2 | [MaaBH2](https://github.com/freeze-12/MaaBH2) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Ffreeze-12%2FMaaBH2%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/freeze-12/MaaBH2/commits) | [`v0.3.6`](https://github.com/freeze-12/MaaBH2/releases/tag/v0.3.6) |
| 崩坏学园 2（可选） | [Honkai2Automation](https://github.com/lolineet/Honkai2Automation) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Flolineet%2FHonkai2Automation%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/lolineet/Honkai2Automation/commits) | 按需单独配置 |
| 明日方舟：终末地 | [MaaEnd](https://github.com/MaaEnd/MaaEnd) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2FMaaEnd%2FMaaEnd%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/MaaEnd/MaaEnd/commits) | [`v3.2.0`](https://github.com/MaaEnd/MaaEnd/releases/tag/v3.2.0) |
| NIKKE 国际服 | [NIKKEAutoScript（NKAS）](https://github.com/megumiss/NIKKEAutoScript) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fmegumiss%2FNIKKEAutoScript%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/megumiss/NIKKEAutoScript/commits) | [`v1.2.0`](https://github.com/megumiss/NIKKEAutoScript/releases/tag/v1.2.0) |
| 学园偶像大师 | [MaaGakumasu](https://github.com/SuperWaterGod/MaaGakumasu) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2FSuperWaterGod%2FMaaGakumasu%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/SuperWaterGod/MaaGakumasu/commits) | [`v1.5.4`](https://github.com/SuperWaterGod/MaaGakumasu/releases/tag/v1.5.4) |
| Dot Abyss | [MaaDotAbyss](https://github.com/Azure-Sora/MaaDotAbyss) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2FAzure-Sora%2FMaaDotAbyss%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/Azure-Sora/MaaDotAbyss/commits) | [`8ec90d7`](https://github.com/Azure-Sora/MaaDotAbyss/commit/8ec90d7b900b9feaaac35cd78498e928e2e2a067) |

<details>
<summary>运行框架和 Python 依赖的提交时间</summary>

公主连结与 Dot Abyss 的适配器使用 MaaFramework `5.16.1`。其他 MFW 项目的运行环境由 AUTO-MAS 按项目准备。Hub 本地后端和 UU 前置任务的版本见 [Python 依赖清单](requirements.txt) 和 [UU 依赖清单](scripts/uu-requirements.txt)。PySide6、其 Addons / Essentials 和 Shiboken6 共用源码仓库。

| 上游源码 | Git 最新提交（UTC） |
| --- | --- |
| [MaaFramework](https://github.com/MaaXYZ/MaaFramework) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2FMaaXYZ%2FMaaFramework%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/MaaXYZ/MaaFramework/commits) |
| [pywinauto](https://github.com/pywinauto/pywinauto) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fpywinauto%2Fpywinauto%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/pywinauto/pywinauto/commits) |
| [RapidOCR](https://github.com/RapidAI/RapidOCR) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2FRapidAI%2FRapidOCR%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/RapidAI/RapidOCR/commits) |
| [ok-script](https://github.com/ok-oldking/ok-script) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fok-oldking%2Fok-script%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/ok-oldking/ok-script/commits) |
| [PyYAML](https://github.com/yaml/pyyaml) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fyaml%2Fpyyaml%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/yaml/pyyaml/commits) |
| [adbutils](https://github.com/openatx/adbutils) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fopenatx%2Fadbutils%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/openatx/adbutils/commits) |
| [pynput](https://github.com/moses-palmer/pynput) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fmoses-palmer%2Fpynput%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/moses-palmer/pynput/commits) |
| [OnnxOCR PP-OCRv5](https://github.com/ok-oldking/OnnxOCR) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fok-oldking%2FOnnxOCR%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/ok-oldking/OnnxOCR/commits) |
| [OpenVINO](https://github.com/openvinotoolkit/openvino) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fopenvinotoolkit%2Fopenvino%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/openvinotoolkit/openvino/commits) |
| [opencv-python](https://github.com/opencv/opencv-python) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fopencv%2Fopencv-python%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/opencv/opencv-python/commits) |
| [OpenCC](https://github.com/BYVoid/OpenCC) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2FBYVoid%2FOpenCC%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/BYVoid/OpenCC/commits) |
| [PySide6 Fluent Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets/tree/PySide6) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2FzhiyiYo%2FPyQt-Fluent-Widgets%2Fcommits%2FPySide6&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/zhiyiYo/PyQt-Fluent-Widgets/commits/PySide6/) |
| [requests](https://github.com/psf/requests) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fpsf%2Frequests%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/psf/requests/commits) |
| [urllib3](https://github.com/urllib3/urllib3) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Furllib3%2Furllib3%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/urllib3/urllib3/commits) |
| [certifi](https://github.com/certifi/python-certifi) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fcertifi%2Fpython-certifi%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/certifi/python-certifi/commits) |
| [charset-normalizer](https://github.com/jawah/charset_normalizer) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fjawah%2Fcharset_normalizer%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/jawah/charset_normalizer/commits) |
| [idna](https://github.com/kjd/idna) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fkjd%2Fidna%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/kjd/idna/commits) |
| [retry2](https://github.com/eSAMTrade/retry) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2FeSAMTrade%2Fretry%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/eSAMTrade/retry/commits) |
| [NumPy](https://github.com/numpy/numpy) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fnumpy%2Fnumpy%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/numpy/numpy/commits) |
| [Pillow](https://github.com/python-pillow/Pillow) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fpython-pillow%2FPillow%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/python-pillow/Pillow/commits) |
| [pyclipper](https://github.com/fonttools/pyclipper) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Ffonttools%2Fpyclipper%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/fonttools/pyclipper/commits) |
| [Shapely](https://github.com/shapely/shapely) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fshapely%2Fshapely%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/shapely/shapely/commits) |
| [OpenVINO Telemetry](https://github.com/openvinotoolkit/telemetry) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fopenvinotoolkit%2Ftelemetry%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/openvinotoolkit/telemetry/commits) |
| [darkdetect](https://github.com/albertosottile/darkdetect) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Falbertosottile%2Fdarkdetect%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/albertosottile/darkdetect/commits) |
| [PySide6 Frameless Window](https://github.com/zhiyiYo/PyQt-Frameless-Window/tree/PySide6) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2FzhiyiYo%2FPyQt-Frameless-Window%2Fcommits%2FPySide6&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/zhiyiYo/PyQt-Frameless-Window/commits/PySide6/) |
| [pywin32](https://github.com/mhammond/pywin32) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fmhammond%2Fpywin32%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/mhammond/pywin32/commits) |
| [pycaw](https://github.com/AndreMiras/pycaw) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2FAndreMiras%2Fpycaw%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/AndreMiras/pycaw/commits) |
| [comtypes](https://github.com/enthought/comtypes) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fenthought%2Fcomtypes%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/enthought/comtypes/commits) |
| [psutil](https://github.com/giampaolo/psutil) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fgiampaolo%2Fpsutil%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/giampaolo/psutil/commits) |
| [mouse](https://github.com/boppreh/mouse) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fboppreh%2Fmouse%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/boppreh/mouse/commits) |
| [PyDirectInput](https://github.com/learncodebygaming/pydirectinput) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Flearncodebygaming%2Fpydirectinput%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/learncodebygaming/pydirectinput/commits) |
| [decorator](https://github.com/micheles/decorator) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fmicheles%2Fdecorator%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/micheles/decorator/commits) |
| [deprecation](https://github.com/briancurtin/deprecation) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fbriancurtin%2Fdeprecation%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/briancurtin/deprecation/commits) |
| [packaging](https://github.com/pypa/packaging) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fpypa%2Fpackaging%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/pypa/packaging/commits) |
| [six](https://github.com/benjaminp/six) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fbenjaminp%2Fsix%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/benjaminp/six/commits) |
| [typing-extensions](https://github.com/python/typing_extensions) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fpython%2Ftyping_extensions%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/python/typing_extensions/commits) |
| [PyAppify Python](https://github.com/ok-oldking/pyappify-python) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fok-oldking%2Fpyappify-python%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/ok-oldking/pyappify-python/commits) |
| [Brotli](https://github.com/google/brotli) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fgoogle%2Fbrotli%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/google/brotli/commits) |
| [tqdm](https://github.com/tqdm/tqdm) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Ftqdm%2Ftqdm%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/tqdm/tqdm/commits) |
| [Playwright for Python](https://github.com/microsoft/playwright-python) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fmicrosoft%2Fplaywright-python%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/microsoft/playwright-python/commits) |
| [UnityPy](https://github.com/K0lb3/UnityPy) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2FK0lb3%2FUnityPy%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/K0lb3/UnityPy/commits) |
| [PySide6 / Shiboken6](https://github.com/qtproject/pyside-pyside-setup) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fqtproject%2Fpyside-pyside-setup%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/qtproject/pyside-pyside-setup/commits) |
| [OpenAI Python SDK](https://github.com/openai/openai-python) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fopenai%2Fopenai-python%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/openai/openai-python/commits) |
| [ONNX Runtime](https://onnxruntime.ai/) | 2026-11-28 查询时，[官方 GitHub 仓库](https://github.com/microsoft/onnxruntime)返回 404。可查 [PyPI 发行记录](https://pypi.org/project/onnxruntime/#history)。 |

</details>

<details>
<summary>安装工具和 CI 依赖的提交时间</summary>

| 上游源码 | Git 最新提交（UTC） |
| --- | --- |
| [PyAppify](https://github.com/ok-oldking/pyappify) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fok-oldking%2Fpyappify%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/ok-oldking/pyappify/commits) |
| [PyAppify Action](https://github.com/ok-oldking/pyappify-action) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fok-oldking%2Fpyappify-action%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/ok-oldking/pyappify-action/commits) |
| [partial-sync-repo](https://github.com/ok-oldking/partial-sync-repo) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fok-oldking%2Fpartial-sync-repo%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/ok-oldking/partial-sync-repo/commits) |
| [actions/checkout](https://github.com/actions/checkout) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Factions%2Fcheckout%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/actions/checkout/commits) |
| [actions/setup-python](https://github.com/actions/setup-python) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Factions%2Fsetup-python%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/actions/setup-python/commits) |
| [action-gh-release](https://github.com/softprops/action-gh-release) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fsoftprops%2Faction-gh-release%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/softprops/action-gh-release/commits) |
| [Mirror 酱上传 Action](https://github.com/MirrorChyan/uploading-action) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2FMirrorChyan%2Fuploading-action%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/MirrorChyan/uploading-action/commits) |
| [Mirror 酱发布说明 Action](https://github.com/MirrorChyan/release-note-action) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2FMirrorChyan%2Frelease-note-action%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/MirrorChyan/release-note-action/commits) |
| [Git for Windows](https://github.com/git-for-windows/git) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fgit-for-windows%2Fgit%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/git-for-windows/git/commits) |
| [CPython](https://github.com/python/cpython) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fpython%2Fcpython%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/python/cpython/commits) |
| [WinGet](https://github.com/microsoft/winget-cli) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fmicrosoft%2Fwinget-cli%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/microsoft/winget-cli/commits) |
| [curl](https://github.com/curl/curl) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fcurl%2Fcurl%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/curl/curl/commits) |
| [uv](https://github.com/astral-sh/uv) | [![Git 最新提交时间](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2Fastral-sh%2Fuv%2Fcommits%2FHEAD&query=%24.commit.committer.date&label=&style=flat-square)](https://github.com/astral-sh/uv/commits) |
| [Android ADB](https://android.googlesource.com/platform/packages/modules/adb/) | [2025-03-26T00:41:28Z（AOSP main 快照）](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9) · [实时提交记录](https://android.googlesource.com/platform/packages/modules/adb/+log/refs/heads/main) |

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
