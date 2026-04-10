# Qwen3 Voice Studio

> 多模型語音工作站 — 基於 Qwen3-TTS，支援 CustomVoice / VoiceDesign / VoiceClone 三種模式，Workflow 串聯生產流程，SRT 字幕自動生成。

## 功能特色

- 🎙️ **Custom Voice** — 從 9 種內建音色（Vivian、Dylan 等）快速合成
- 🎨 **Voice Design** — 用自然語言描述音色風格，AI 生成對應聲音
- 🔁 **Voice Clone** — 上傳 3–10 秒參考音頻，克隆任意音色
- ⚡ **Workflow** — 三步驟串聯：設計音色 → 克隆 → 批量匯出
- 📦 **批量合成** — 上傳 .txt/.md 一鍵生成多段 WAV + SRT
- 📝 **SRT 字幕** — sentence-level 自動生成（均勻分配 / 語速估算）
- 🌐 **雙語 GUI** — 繁體中文（預設）/ English
- 🖥️ **CUDA 推論** — RTX 3060 Ti 等 NVIDIA GPU 全速推論

## 快速開始

### 1. 安裝 uv

```powershell
# Windows PowerShell
irm https://astral.sh/uv/install.ps1 | iex
```

### 2. 安裝依賴並啟動

```powershell
# Windows
.\start.ps1

# Linux / macOS
bash start.sh

# 手動
uv sync
uv run python app.py
```

### 3. 首次使用各 Tab

每個 Tab 首次點擊生成時，會自動下載對應模型（約 1–2 GB）到：

```
~/.cache/qwen3-voice-studio/
```

| Tab | 自動下載的模型 | 大小 |
|-----|-------------|------|
| Custom Voice | `Qwen3-TTS-12Hz-0.6B-CustomVoice` | ~1.2 GB |
| Voice Design | `Qwen3-TTS-12Hz-0.6B-VoiceDesign` | ~1.2 GB |
| Voice Clone / Workflow | `Qwen3-TTS-12Hz-0.6B-Base` | ~1.2 GB |

## 模型說明

| 模式 | 模型 | 用途 |
|------|------|------|
| Custom Voice | `Qwen3-TTS-12Hz-0.6B-CustomVoice` | 9 種具名音色，可搭配風格指令 |
| Voice Design | `Qwen3-TTS-12Hz-0.6B-VoiceDesign` | 自然語言描述音色 |
| Voice Clone | `Qwen3-TTS-12Hz-0.6B-Base` | 3–10 秒參考音頻克隆 |

也支援 1.7B 高品質版本（需更多 VRAM），可在設定頁切換。

## Workflow 三步驟

```
Step 1  Voice Design  →  描述音色原型（e.g. "溫柔的女聲"）→ 試聽音頻
Step 2  Voice Clone   →  以 Step 1 音頻為參考，克隆到新文字
Step 3  Batch Export  →  批量套用克隆音色到多段文字，匯出 WAV + SRT
```

## 系統需求

| 項目 | 最低 | 建議 |
|------|------|------|
| Python | 3.10 | 3.11 |
| GPU | NVIDIA 4GB VRAM | 8GB（可同時承載 2–3 個 0.6B 模型） |
| RAM | 8GB | 16GB |
| CUDA | 11.8+ | 12.4（cu124） |

## 開發指令

```bash
uv run ruff check . --fix  # Lint
uv run pytest -v           # 測試
```

## 授權

MIT License
