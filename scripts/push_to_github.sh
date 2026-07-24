#!/usr/bin/env bash
# 推送 daily-clear-hub 到 https://github.com/electrovalentbond
set -euo pipefail

export https_proxy="${https_proxy:-http://127.0.0.1:7890}"
export http_proxy="${http_proxy:-http://127.0.0.1:7890}"

REPO="electrovalentbond/daily-clear-hub"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GH="${GH:-/opt/homebrew/bin/gh}"

cd "$ROOT"

if ! "$GH" auth status >/dev/null 2>&1; then
  echo "请先登录 GitHub："
  echo "  export https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890"
  echo "  $GH auth login --hostname github.com --git-protocol https --web --skip-ssh-key"
  echo "在浏览器打开 https://github.com/login/device 输入终端显示的设备码。"
  exit 1
fi

if ! "$GH" repo view "$REPO" >/dev/null 2>&1; then
  echo "创建远程仓库 $REPO ..."
  "$GH" repo create "$REPO" --public --description "多游戏日常统一自动化 (ok-script)" --source=. --remote=origin
else
  git remote remove origin 2>/dev/null || true
  git remote add origin "https://github.com/${REPO}.git"
fi

git -c http.postBuffer=524288000 push -u origin main
echo "完成: https://github.com/${REPO}"
