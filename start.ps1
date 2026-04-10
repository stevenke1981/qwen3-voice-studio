# Qwen3 Voice Studio — Windows 啟動腳本 (PowerShell)
# 用法: .\start.ps1 [--port 7860] [--share] [--demo]

param(
    [int]$Port = 7860,
    [switch]$Share,
    [switch]$Demo
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "=== Qwen3 Voice Studio ===" -ForegroundColor Cyan

# 1. 確認 uv 已安裝
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] uv not found. Install via: winget install astral-sh.uv" -ForegroundColor Red
    Write-Host "        or: irm https://astral.sh/uv/install.ps1 | iex" -ForegroundColor Yellow
    exit 1
}

$uvVersion = (uv --version) 2>&1
Write-Host "[OK] $uvVersion" -ForegroundColor Green

# 2. 若無 .venv，自動建立並安裝依賴
if (-not (Test-Path ".venv")) {
    Write-Host "[SETUP] 建立虛擬環境..." -ForegroundColor Yellow
    uv venv --python 3.10
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

# 3. 同步依賴（含 dev）
Write-Host "[SETUP] 同步依賴套件..." -ForegroundColor Yellow
uv sync --extra gpu
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] GPU 依賴安裝失敗，嘗試基本依賴..." -ForegroundColor Yellow
    uv sync
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

# 4. 組裝啟動參數
$appArgs = @("--port", $Port)
if ($Share) { $appArgs += "--share" }
if ($Demo)  { $appArgs += "--demo" }

# 5. 啟動應用
Write-Host "[START] 啟動 Qwen3 Voice Studio (port: $Port)..." -ForegroundColor Green
uv run python app.py @appArgs
