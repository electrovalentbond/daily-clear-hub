# Daily Clear Hub

多游戏日常统一自动化：基于 [ok-script](https://github.com/ok-oldking/ok-script)，PC 端 Win32 + 模拟器 ADB 一套代码。

仓库：https://github.com/electrovalentbond/daily-clear-hub

## 开发环境

| 环境 | 用途 |
|------|------|
| **macOS** | 写 Python 逻辑、跑 `run_tests.sh` 截图无关单测 |
| **Windows** | 真游戏/雷电联调、`main_debug.py`、PyAppify 打包 |

> ok-script 运行时依赖 Win32，**无法在 macOS 上控制游戏**。完整 E2E 请在 Windows（实体机或 Parallels）验证。

## 快速开始

### macOS（逻辑开发）

```bash
git clone https://github.com/electrovalentbond/daily-clear-hub.git
cd daily-clear-hub
python3 -m venv .venv && source .venv/bin/activate
pip install pyyaml
./run_tests.sh
```

完整依赖（含 ok-script）需在 **Windows + Python 3.12** 安装。

### Windows（联调 / 运行）

**前置：** Python 3.12、Git、雷电模拟器 9（公主连结）、已安装的 PC 游戏（崩坏3 等）。

```powershell
git clone https://github.com/electrovalentbond/daily-clear-hub.git
cd daily-clear-hub
py -3.12 -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy config.local.yaml.example config.local.yaml
notepad config.local.yaml
```

`config.local.yaml` 示例：

```yaml
windows:
  honkai3_exe: "D:/Games/bh3/launcher.exe"
emulator:
  ldplayer_root: "C:/leidian/LDPlayer9"
  adb: "C:/leidian/LDPlayer9/adb.exe"
```

**必须**右键「以管理员身份运行」终端或 IDE，然后：

```powershell
python main_debug.py
```

Phase 0 验证清单：

1. GUI 里「截图测试」成功
2. 「诊断任务」可运行
3. 雷电开启 USB 调试后 `adb devices` 有设备
4. 任务列表可见：崩坏3 日常 / 公主连结 日常 / 一键清日常

日常更新：

```powershell
git pull
pip install -r requirements.txt
python main_debug.py
```

## 配置

- `config.yaml`：任务开关、调度顺序（提交 Git）
- `config.local.yaml`：本机 Windows 路径（复制 example，**不提交**）
- `accounts.yaml`：多账号（可选，复制 `accounts.yaml.example`）

各游戏步骤开关在 ok-script GUI 对应任务内勾选（如「材料远征」「收取礼物」）。

## 项目结构

```
core/           调度器、配置加载、雷电封装
games/          各游戏 Plugin 与 Task（steps / features）
src/            ok-script 应用配置与入口 Task
assets/         模板图（Windows 联调后补充，见 features.py）
config.yaml     全局调度配置
tests/          macOS 可跑的单元测试
```

## mac ↔ Windows 协作

| 环境 | 做什么 |
|------|--------|
| macOS | 写逻辑 → `./run_tests.sh` → `git push` |
| Windows | `git pull` → 真机联调 → 补 `assets/` → `git push` |

模板特征名见：

- `games/honkai3/features.py`
- `games/pcr/features.py`

公主连结建议分辨率：**540×960 DPI 240**；崩坏3 PC：**1920×1080** 16:9。

## Windows 交付

- 开发期：`git pull` + `python main.py`
- 产品化：配置 `pyappify.yml`，打 `v*` tag 由 GitHub Actions 构建 `setup.exe`

## 当前进度

- [x] ok-script 模板 + `core/` 调度器骨架
- [x] `config.yaml` / `config.local.yaml` 分离
- [x] 崩坏3 MVP 日常步骤（材料远征/家园/舰团/领奖）
- [x] 公主连结 MVP 日常步骤（礼物/任务/扫荡/地下城/捐赠）
- [x] 代码已推送到 GitHub
- [ ] Windows Phase 0 环境验证
- [ ] 补充 `assets/` 模板图并真实联调
- [ ] 截图回归测试（`TaskTestCase`）
