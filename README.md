# Daily Clear Hub

多游戏日常统一自动化：基于 [ok-script](https://github.com/ok-oldking/ok-script)，PC 端 Win32 + 模拟器 ADB 一套代码。

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

完整依赖（含 ok-script）需在 **Windows + Python 3.12** 安装：

```bash
pip install -r requirements.txt
```

### Windows（联调 / 运行）

```powershell
git clone <your-repo> daily-clear-hub
cd daily-clear-hub
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy config.local.yaml.example config.local.yaml
# 编辑 config.local.yaml 填写游戏 exe 与雷电路径
# 以管理员身份运行 IDE 或终端
python main_debug.py
```

## 配置

- `config.yaml`：任务开关、调度顺序（提交 Git）
- `config.local.yaml`：本机 Windows 路径（复制 example，不提交）
- `accounts.yaml`：多账号（可选，复制 `accounts.yaml.example`）

## 项目结构

```
core/           调度器、配置加载、雷电封装
games/          各游戏 Plugin 与 Task
src/            ok-script 应用配置与入口 Task
config.yaml     全局调度配置
tests/          macOS 可跑的单元测试
```

## Windows 交付

- 开发期：`git pull` + `python main.py`
- 产品化：配置 `pyappify.yml`，打 `v*` tag 由 GitHub Actions 构建 `setup.exe`

## 当前进度（MVP 骨架）

- [x] ok-script 模板 + `core/` 调度器骨架
- [x] `config.yaml` / `config.local.yaml` 分离
- [x] 崩坏3 MVP 日常步骤（材料远征/家园/舰团/领奖，参考 Maa_bbb）
- [x] 公主连结 MVP 日常步骤（礼物/任务/扫荡/地下城/捐赠，参考 farm）
- [ ] Windows 联调：补充 `assets/` 模板图（见 `games/*/features.py`）
- [ ] 真实截图回归测试（`TaskTestCase`）
