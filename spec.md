# qwen3-voice-studio — 技術規格

> 最後更新：2026-04-11 — 多模型 Workflow 架構

## 1. 產品原則

- **三模型分頁**：每種 model_type 對應獨立 Tab
- **Workflow 串聯**：VoiceDesign → VoiceClone → Batch 三步驟 pipeline
- **CUDA 優先**：預設 `cuda:0`，懶載入各模型
- **SRT sentence-level**：文字斷句 + 總時長比例估算，不依賴對齊模型
- **繁體中文 GUI**：預設 zh-TW，可切換 en

## 2. 系統需求

| 項目 | 最低 | 建議 |
|------|------|------|
| Python | 3.10 | 3.11 |
| GPU VRAM | 4GB | 8GB（3060 Ti 可同時承載 2–3 個 0.6B） |
| RAM | 8GB | 16GB |
| OS | Windows 10 / Linux | |
| uv | 0.11+ | 最新穩定版 |

## 3. 模型規格

### 3.1 三種模型類型

| 類型 | model_type | 核心方法 | 主要用途 |
|------|-----------|---------|---------|
| CustomVoice | `custom_voice` | `generate_custom_voice` | 內建 9 種具名音色（Vivian, Serena, ...） |
| VoiceDesign | `voice_design` | `generate_voice_design` | 自然語言描述音色風格 |
| Base | `base` | `generate_voice_clone` | 上傳參考音頻克隆音色 |

### 3.2 預設模型 ID（0.6B 系列）

```python
MODEL_CUSTOM_VOICE = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
MODEL_VOICE_DESIGN = "Qwen/Qwen3-TTS-12Hz-0.6B-VoiceDesign"
MODEL_BASE         = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
```

### 3.3 大模型變體（1.7B，高品質，需更多 VRAM）

```python
MODEL_CUSTOM_VOICE_LG = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
MODEL_VOICE_DESIGN_LG = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
MODEL_BASE_LG         = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
```

## 4. 核心架構

### 4.1 ModelPool（`src/multi_engine.py`）

```python
@dataclass
class ModelPool:
    custom_voice_path: str
    voice_design_path: str
    base_path: str
    device: str = "cuda:0"
    _engines: dict[str, TTSEngine] = ...

    def get(self, kind: str) -> TTSEngine:
        """懶載入：首次呼叫才下載 + 載入，後續直接回傳快取"""
```

- 各 Tab 呼叫 `model_pool.get("custom_voice")` / `get("voice_design")` / `get("base")`
- 首次使用自動觸發 `ensure_tts_model_available` 下載模型

### 4.2 TTSEngine（`src/tts_engine.py`）

- 包裝單一 `Qwen3TTSModel` 實例
- 載入後偵測 `model.tts_model_type` 並儲存
- `synthesize()` → 要求 `custom_voice`
- `voice_design()` → 要求 `voice_design`
- `voice_clone()` → 要求 `base`
- 型別不符直接拋出 `RuntimeError`（防止靜默失敗）

### 4.3 GUI Tab 結構

```
gui/
├── app_ui.py           主 Blocks 組裝
├── workflow_tab.py     ⚡ Workflow（三步驟串聯）← 首頁
├── custom_voice_tab.py 🎙️ Custom Voice
├── voice_design_tab.py 🎨 Voice Design
├── voice_clone_tab.py  🔁 Voice Clone
├── batch_tab.py        📦 批量合成（CustomVoice）
├── history_tab.py      📜 歷史記錄
├── settings_tab.py     ⚙️ 設定（三模型路徑）
├── monitor_tab.py      📊 效能監控
└── error_panel.py      🔴 錯誤日誌
```

## 5. Workflow Tab 規格

三個可獨立/串聯的步驟：

```
Step 1: Voice Design
  inputs:  design_text, instruct, language
  outputs: audio_preview, ref_audio_path (傳給 Step 2)
  model:   VoiceDesign

Step 2: Voice Clone
  inputs:  clone_text, ref_audio_path (來自 Step 1 或手動上傳)
  outputs: cloned_audio, cloned_ref_path (傳給 Step 3)
  model:   Base

Step 3: Batch Export
  inputs:  multiline_texts, cloned_ref_path, srt_mode
  outputs: wav_files[], srt_files[]
  model:   Base（批量 voice_clone）
```

## 6. SRT 規格

- 粒度：sentence-level
- 模式 A：均勻分配 `duration / n`
- 模式 B：語速估計（中文 160 字/分，英文 150 詞/分）
- 格式：UTF-8，`HH:MM:SS,mmm`

## 7. 相依版本鎖定

```toml
qwen-tts = "0.1.1"
transformers = "4.57.3"          # qwen-tts 依賴
huggingface-hub = ">=0.34,<1.0"  # transformers 4.57.3 限制
onnxruntime = "<1.24"            # Python 3.10 無 cp310 wheel for 1.24+
torch = "2.6.0+cu124"            # CUDA 12.4，RTX 3060 Ti
```

## 8. 音訊安全轉換

Gradio 的 float32→int16 轉換在全零音訊時會 division-by-zero。
解法：`to_gradio_audio(audio, sr)` 在傳給 Gradio 前自行正規化：

```python
def to_gradio_audio(audio, sample_rate):
    max_val = np.abs(audio).max()
    if max_val > 0:
        audio = audio / max_val
    return sample_rate, np.clip(audio * 32767, -32768, 32767).astype(np.int16)
```

## 9. 驗收標準

- [ ] 三個 Tab 各自能推論（需下載三個模型）
- [ ] Workflow 三步驟串聯正常
- [ ] Base VoiceClone 已驗證（duration=4.64s，CUDA RTX 3060 Ti）
- [ ] WAV + SRT 雙輸出
- [ ] `uv run python app.py` 無 ERROR 啟動
- [ ] GitHub 公開 repo 已推送
