# qwen3-voice-studio — Knowledge Graph

> 最後更新：2026-04-11 — 多模型 Workflow 架構

## 節點（Nodes）

### 應用程式層

| 節點 | 類型 | 說明 |
|------|------|------|
| `app.py` | EntryPoint | 啟動點，初始化 ModelPool + Gradio |
| `gui/app_ui.py` | UIOrchestrator | 組裝所有 Tab 為 gr.Blocks |

### GUI 分頁

| 節點 | Tab 名稱 | 使用模型 |
|------|---------|---------|
| `gui/workflow_tab.py` | ⚡ Workflow | VoiceDesign + Base（串聯） |
| `gui/custom_voice_tab.py` | 🎙️ Custom Voice | CustomVoice |
| `gui/voice_design_tab.py` | 🎨 Voice Design | VoiceDesign |
| `gui/voice_clone_tab.py` | 🔁 Voice Clone | Base |
| `gui/batch_tab.py` | 📦 批量合成 | CustomVoice |
| `gui/history_tab.py` | 📜 歷史記錄 | — |
| `gui/settings_tab.py` | ⚙️ 設定 | — |
| `gui/monitor_tab.py` | 📊 監控 | — |
| `gui/error_panel.py` | 🔴 錯誤日誌 | — |

### 核心引擎

| 節點 | 類型 | 說明 |
|------|------|------|
| `src/multi_engine.py::ModelPool` | ModelPool | 懶載入三種模型的池 |
| `src/tts_engine.py::TTSEngine` | Engine | 單一模型封裝，含 model_type 路由 |
| `src/config.py::TTSSettings` | Config | 三模型路徑 + CUDA 設定 |
| `src/model_manager.py` | ModelManager | HF 下載 + 快取管理 |
| `src/audio_utils.py::to_gradio_audio` | Utility | 安全 float32→int16 轉換 |
| `src/history.py::HistoryManager` | History | 合成記錄管理 |
| `src/voice_library.py::VoiceLibrary` | VoiceLib | 自訂音色庫 |
| `utils/srt_generator.py` | SRTGenerator | Sentence-level SRT 生成 |

### 外部依賴

| 節點 | 版本 | 說明 |
|------|------|------|
| `qwen-tts` | 0.1.1 | Qwen3 TTS 推論套件 |
| `transformers` | 4.57.3 | HuggingFace Transformers（qwen-tts 依賴） |
| `torch` | 2.6.0+cu124 | CUDA 12.4 推論 |
| `huggingface-hub` | >=0.34,<1.0 | 模型下載（版本限制） |
| `onnxruntime` | <1.24 | Python 3.10 相容性限制 |
| `gradio` | >=5.0 | GUI 框架 |

### Qwen3-TTS 模型節點

| 節點 | model_type | 方法 |
|------|-----------|------|
| `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice` | `custom_voice` | `generate_custom_voice` |
| `Qwen/Qwen3-TTS-12Hz-0.6B-VoiceDesign` | `voice_design` | `generate_voice_design` |
| `Qwen/Qwen3-TTS-12Hz-0.6B-Base` | `base` | `generate_voice_clone` |
| `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` | `custom_voice` | `generate_custom_voice` |
| `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign` | `voice_design` | `generate_voice_design` |
| `Qwen/Qwen3-TTS-12Hz-1.7B-Base` | `base` | `generate_voice_clone` |

## 邊（Edges）

### 呼叫關係

```
app.py
  └─ initializes ──→ ModelPool
  └─ initializes ──→ ErrorHandler, HistoryManager, VoiceLibrary
  └─ builds ───────→ gui/app_ui.py::build_app

gui/app_ui.py
  └─ builds ───────→ workflow_tab, custom_voice_tab, voice_design_tab,
                      voice_clone_tab, batch_tab, history_tab,
                      settings_tab, monitor_tab, error_panel

gui/workflow_tab.py
  └─ calls ────────→ ModelPool.get("voice_design") → TTSEngine.voice_design()
  └─ calls ────────→ ModelPool.get("base") → TTSEngine.voice_clone()

gui/custom_voice_tab.py
  └─ calls ────────→ ModelPool.get("custom_voice") → TTSEngine.synthesize()

gui/voice_design_tab.py
  └─ calls ────────→ ModelPool.get("voice_design") → TTSEngine.voice_design()

gui/voice_clone_tab.py
  └─ calls ────────→ ModelPool.get("base") → TTSEngine.voice_clone()

gui/batch_tab.py
  └─ calls ────────→ ModelPool.get("custom_voice") → TTSEngine.synthesize()
```

### 資料流（Workflow Tab）

```
User Input (text + instruct)
  → Step 1: VoiceDesign Engine → audio_preview + tmp_wav_path
  → Step 2: Base Engine (ref=tmp_wav) → cloned_audio + cloned_ref_path
  → Step 3: Base Engine (batch) → N×WAV + N×SRT
```

### 模型懶載入流

```
ModelPool.get("base")
  → 檢查 _engines["base"] 是否存在
  → 不存在：model_manager.ensure_tts_model_available(base_path)
    → 若未下載：huggingface_hub.snapshot_download()
    → 下載至：~/.cache/qwen3-voice-studio/
  → TTSEngine(model_path=base_path, device="cuda:0").load_model()
    → Qwen3TTSModel.from_pretrained(..., dtype=bfloat16)
    → 偵測 model.tts_model_type = "base"
  → 快取至 _engines["base"]
  → 返回 TTSEngine
```

## 關鍵限制與決策

| 決策 | 原因 |
|------|------|
| 每種 model_type 獨立 Tab | qwen-tts 的每個生成方法只接受對應 model_type，混用會 RuntimeError |
| transformers==4.57.3（非 4.57.6） | qwen-tts 0.1.1 的 metadata 鎖定此版本 |
| huggingface-hub<1.0 | transformers 4.57.3 的 dependency_versions_check 要求 |
| onnxruntime<1.24 | Python 3.10 在 1.24+ 無 cp310 wheel |
| torch cu124 from PyTorch index | pyproject.toml 的 `[[tool.uv.index]]` 指向官方 CUDA wheel |
| to_gradio_audio() 預轉換 | Gradio processing_utils 對全零音訊有 division-by-zero bug |
| WinError 10054 過濾 | Windows asyncio proactor 關閉已斷線 socket 的正常行為，非應用錯誤 |
