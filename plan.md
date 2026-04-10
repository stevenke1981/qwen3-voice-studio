# qwen3-voice-studio — 開發計畫

> 最後更新：2026-04-11 — 多模型 Workflow GUI 架構完成

## 專案定位

**qwen3-voice-studio** 是一個面向專業內容創作者、配音與長文 TTS 工作流的 GUI 應用，
基於 Qwen3-TTS 三種模型類型，以 Gradio Workflow 串聯完整語音生產流程。

## 架構原則

- **三模型分頁**：每個模型類型對應獨立 Tab，不互相干擾
- **Workflow 串聯**：VoiceDesign → VoiceClone → BatchExport 三步驟 pipeline
- **懶載入**：各 Tab 首次使用時才下載並載入對應模型
- **CUDA 優先**：預設 `cuda:0`，RTX 3060 Ti 可同時承載多個 0.6B 模型
- **SRT sentence-level**：不依賴對齊模型，純文字斷句 + 總時長比例分配

## 模型對應表

| Tab | 模型 ID | model_type | 核心方法 |
|-----|---------|------------|---------|
| Custom Voice | `Qwen3-TTS-12Hz-0.6B-CustomVoice` | `custom_voice` | `generate_custom_voice` |
| Voice Design | `Qwen3-TTS-12Hz-0.6B-VoiceDesign` | `voice_design` | `generate_voice_design` |
| Voice Clone | `Qwen3-TTS-12Hz-0.6B-Base` | `base` | `generate_voice_clone` |
| Workflow | 三者組合 | — | 串聯 pipeline |
| Batch | CustomVoice | `custom_voice` | 批量 synthesize |

## 目前狀態

### 已完成 ✅

- [x] 三模型分頁 GUI（Custom Voice / Voice Design / Voice Clone）
- [x] Workflow Tab（三步驟串聯）
- [x] ModelPool 懶載入 + VRAM 管理
- [x] TTSEngine model_type 路由（防止錯誤模型呼叫錯誤方法）
- [x] CUDA torch 安裝（2.6.0+cu124，RTX 3060 Ti）
- [x] qwen-tts + transformers + 相依套件安裝
- [x] VoiceClone 驗證（`duration=4.64s`，int16 max=32767）
- [x] Gradio float32 → int16 安全轉換（`to_gradio_audio`）
- [x] WinError 10054 asyncio 噪訊過濾
- [x] settings_tab 支援三模型路徑設定
- [x] pyproject.toml 鎖定相依版本（transformers==4.57.3、onnxruntime<1.24、hub<1.0）
- [x] GitHub 公開 repo 推送

### 待確認 ⚠️

- [ ] CustomVoice 模型下載後的真實推論測試
  - 需下載 `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice`
- [ ] VoiceDesign 模型下載後的真實推論測試
  - 需下載 `Qwen/Qwen3-TTS-12Hz-0.6B-VoiceDesign`
- [ ] 長文批量穩定性測試
- [ ] `uv run ruff check . --fix` 全綠
- [ ] `uv run pytest -v` 全綠

## 啟動方式

```bash
# 標準啟動（預先載入 Base 模型）
uv run python app.py

# Demo 模式（不載入任何模型）
uv run python app.py --demo

# 自訂 port
uv run python app.py --port 8080
```

## 模型下載路徑

首次使用各 Tab 時自動下載到：
```
~/.cache/qwen3-voice-studio/
```

Windows：`C:\Users\{user}\.cache\qwen3-voice-studio\`

## 技術限制

- qwen-tts 0.1.1 需 transformers==4.57.3（與 hub<1.0 綁定）
- onnxruntime 需 <1.24（Python 3.10 無 cp310 wheel）
- torch CUDA 需從 `https://download.pytorch.org/whl/cu124` 安裝

## 驗收標準

完成時必須符合：

- [ ] 三個 Tab 各自能呼叫對應模型完成推論
- [ ] Workflow Tab 三步驟串聯可正常執行
- [ ] WAV + SRT 可同步輸出
- [ ] CUDA 推論（RTX 3060 Ti）可正常使用
- [ ] `uv run python app.py` 啟動無 ERROR
- [ ] GitHub 公開 repo 已推送
