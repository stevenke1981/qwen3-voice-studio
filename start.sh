#!/usr/bin/env bash
# Qwen3 Voice Studio — Linux / macOS 啟動腳本
# 用法: bash start.sh [--port 7860] [--share] [--demo]

set -euo pipefail

PORT=7860
EXTRA_ARGS=()

# 解析命令列參數
while [[ $# -gt 0 ]]; do
    case "$1" in
        --port)  PORT="$2"; shift 2 ;;
        --share) EXTRA_ARGS+=("--share"); shift ;;
        --demo)  EXTRA_ARGS+=("--demo");  shift ;;
        *) EXTRA_ARGS+=("$1"); shift ;;
    esac
done

echo "=== Qwen3 Voice Studio ==="

# 1. 確認 uv 已安裝
if ! command -v uv &>/dev/null; then
    echo "[ERROR] uv not found. Install via:"
    echo "        curl -Lsf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "[OK] $(uv --version)"

# 2. 若無 .venv，自動建立
if [ ! -d ".venv" ]; then
    echo "[SETUP] 建立虛擬環境..."
    uv venv --python 3.10
fi

# 3. 同步依賴
echo "[SETUP] 同步依賴套件..."
if ! uv sync --extra gpu 2>/dev/null; then
    echo "[WARN] GPU 依賴安裝失敗，嘗試基本依賴..."
    uv sync
fi

# 4. 啟動應用
echo "[START] 啟動 Qwen3 Voice Studio (port: ${PORT})..."
uv run python app.py --port "${PORT}" "${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}"
