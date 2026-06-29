# qwen3-voice-studio — 測試計畫

> 產生日期：2026-06-29
> 依據：CBM 全專案架構分析 (47 檔案, 266 符號, 916 邊) + 現有測試覆蓋率審查

---

## 1. 現有測試覆蓋率總覽

| 模組 | 測試檔案 | 類別/函式 | 行覆蓋率 (估計) | 狀態 |
|------|---------|-----------|----------------|------|
| `src/audio_utils.py` | `test_audio_utils.py` | 3 classes | ~70% | ⚠️ `to_gradio_audio()` 未測試 |
| `src/config.py` | `test_config.py` | 3 classes | ~60% | ❌ `model_path` → `base_model` 測試錯誤 |
| `src/srt_generator.py` | `test_srt.py` | 2 classes | ~80% | ✅ 基本覆蓋 |
| `src/error_handler.py` | `test_error_handler.py` | 1 class | ~80% | ⚠️ 與 VoiceLibrary 測試混在同一檔 |
| `src/history.py` | `test_history.py` | 1 class | ~70% | ✅ 基本覆蓋 |
| `src/i18n.py` | `test_i18n.py` | 4 classes | ~85% | ✅ 良好 |
| `src/voice_library.py` | `test_error_handler.py` | 1 class | ~60% | ⚠️ 應在獨立測試檔 |
| `utils/srt_generator.py` | `test_srt_generator.py` | 9 classes | ~90% | ✅ 優秀 |
| `src/tts_engine.py` | **無** | — | **0%** | ❌ |
| `src/multi_engine.py` | **無** | — | **0%** | ❌ |
| `src/model_manager.py` | **無** | — | **0%** | ❌ |
| `src/monitor.py` | **無** | — | **0%** | ❌ |
| `src/tts_server.py` | **無** | — | **0%** | ❌ |
| `gui/*.py` | **無** | — | **0%** | ⚠️ Gradio UI 需整合測試 |

**總結：** 9 個測試檔，~50 個測試案例，覆蓋約 40% 的模組。

---

## 2. 新增測試優先級

### 🔴 P0 — 必須補上（核心引擎無測試）

#### [T0-01] `tests/test_tts_engine.py` — TTSEngine 單元測試

**測試範圍：**

| 測試目標 | 測試案例 | 說明 |
|---------|---------|------|
| `TTSResult` | 建立與欄位存取 | dataclass 基本測試 |
| `TTSEngine` demo mode | 未載入模型時 `synthesize()` 回傳靜音 | `_model=None, _loaded=False` |
| `TTSEngine` demo mode | 未載入模型時 `voice_design()` 回傳靜音 | 同上 |
| `TTSEngine` demo mode | 未載入模型時 `voice_clone()` 回傳靜音 | 同上 |
| `TTSEngine` model_type 檢查 | `synthesize()` 在非 `custom_voice` 時拋出 `RuntimeError` | |
| `TTSEngine` model_type 檢查 | `voice_design()` 在非 `voice_design` 時拋出 `RuntimeError` | |
| `TTSEngine` model_type 檢查 | `voice_clone()` 在非 `base` 時拋出 `RuntimeError` | |
| `TTSEngine` model_type 檢查 | `voice_clone()` 在 `ref_audio=None` 時拋出 `ValueError` | |
| `TTSEngine.is_loaded()` | 初始為 `False`，load_model 後為 `True` | 需 mock `Qwen3TTSModel` |
| `TTSEngine.model_type` | 載入後回傳正確的 model_type | mock `tts_model_type` |
| `TTSEngine.unload()` | 卸載後 `is_loaded()` 為 `False` | |
| `TTSEngine.to_wav_bytes()` | `TTSResult` → WAV bytes | 驗證 WAV header |
| `TTSEngine.get_supported_speakers()` | 回傳列表或空列表 | mock |
| `TTSEngine.get_supported_languages()` | 回傳語言列表 | mock |

**預計案例數：** ~15

---

#### [T0-02] `tests/test_multi_engine.py` — ModelPool 單元測試

**測試範圍：**

| 測試目標 | 測試案例 |
|---------|---------|
| 初始狀態 | `loaded_kinds()` 為空列表 |
| 初始狀態 | `is_loaded("base")` 為 `False` |
| `get()` 第一次呼叫 | 觸發 engine 建立與載入（mock TTSEngine） |
| `get()` 第二次呼叫 | 回傳快取（不重複建立） |
| `get()` 無效 kind | 拋出 `ValueError` |
| `unload()` | 移除指定引擎 |
| `unload_all()` | 移除所有引擎 |
| `_ensure_downloaded()` | 成功下載不拋出 |
| `_ensure_downloaded()` | 下載失敗只 log warning 不拋出 |

**預計案例數：** ~9

---

#### [T0-03] `tests/test_model_manager.py` — ModelManager 單元測試

**測試範圍：**

| 測試目標 | 測試案例 |
|---------|---------|
| `get_cache_dir()` | 回傳 `Path` 且目錄存在 |
| `is_model_downloaded()` | repo_id 在快取中回傳 `True`（mock scan_cache_dir） |
| `is_model_downloaded()` | repo_id 不在快取中回傳 `False` |
| `is_model_downloaded()` | 本地路徑存在回傳 `True` |
| `download_model()` | 成功下載（mock snapshot_download） |
| `download_model()` | huggingface-hub 未安裝拋出 `RuntimeError` |
| `ensure_tts_model_available()` | 本地路徑存在回傳路徑 |
| `ensure_tts_model_available()` | 模型已快取回傳 ID |
| `ensure_tts_model_available()` | 需下載時觸發下載 |

**預計案例數：** ~9

---

#### [T0-04] `tests/test_monitor.py` — Monitor 測試

**測試範圍：**

| 測試目標 | 測試案例 |
|---------|---------|
| `SystemMetrics` | dataclass 預設值 |
| `format_metrics_display()` | zh-TW 格式輸出包含預期字串 |
| `format_metrics_display()` | en 格式輸出包含預期字串 |
| `format_metrics_display()` | 模型載入狀態顯示正確 |
| `get_system_metrics()` | pynvml 不可用時 graceful fallback |
| `get_system_metrics()` | psutil 不可用時 graceful fallback |

**預計案例數：** ~6

---

### 🟡 P1 — 重要補強

#### [T1-01] `to_gradio_audio()` 邊界測試

**應移至獨立測試類別或在 `test_audio_utils.py` 擴充：**

| 測試案例 | 說明 |
|---------|------|
| 正常音訊 | float32 隨機音訊，驗證回傳 int16 且範圍正確 |
| 全零音訊 | 防止 division-by-zero |
| 單一樣本 | 一個 sample 的邊界 |
| 極大值 | float32 ±1.0 邊界 |
| 極小值 | float32 接近零 |
| 立體聲輸入 | 多聲道需保留（當前實作假設 mono） |

**預計案例數：** ~6

---

#### [T1-02] `src/voice_library.py` 獨立測試檔

將 `test_error_handler.py` 中的 `TestVoiceLibrary` 移至 `tests/test_voice_library.py`：

| 測試案例 | 說明 |
|---------|------|
| 儲存與列出 | ✅ 已有 |
| 刪除 | ✅ 已有 |
| 路徑穿越阻擋 | ✅ 已有 |
| 不存在的音色刪除 | 回傳 `False` |
| 取得不存在的音色 | 回傳 `None` |
| 檔名安全 sanitization | 特殊字元處理 |

**預計案例數：** ~6

---

#### [T1-03] `tests/test_tts_server.py` — TTS Server 測試

| 測試目標 | 測試案例 |
|---------|---------|
| `create_app()` | 回傳 FastAPI app |
| `GET /tts/health` | 回傳 JSON 含 status 與 model_loaded |
| `GET /tts/voices` | 回傳 speakers 與 languages |
| `POST /tts/synthesize` | mock TTSEngine 驗證路由 |
| `TTSServerManager` | start/stop/is_running 狀態轉換 |
| `TTSServerManager` | 重複 start 不崩潰 |

**預計案例數：** ~6

---

### 🟢 P2 — 既有測試修正

#### [T2-01] `test_config.py` 修正

```python
# 錯誤（第 13 行）：
assert s.model_path == "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
# 修正為：
assert s.base_model == "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
```

---

## 3. 整合測試

### [TI-01] Demo 模式端對端測試

在 `tests/` 新增 `test_integration.py`：

| 測試案例 | 說明 |
|---------|------|
| `app.py --demo` 啟動 | 驗證無 ERROR 啟動 |
| ModelPool demo mode | 各引擎回傳靜音而非崩潰 |
| SRT 生成整合 | 文字 → normalize → split → allocate → format → 完整 chain |

### [TI-02] Workflow Chain 邏輯測試

測試「VoiceDesign → VoiceClone → Batch」的資料傳遞邏輯（mock 引擎）：

| 測試案例 | 說明 |
|---------|------|
| Step 1 空輸入 | 回傳錯誤訊息而非崩潰 |
| Step 2 無參考音頻 | 正確提示需先執行 Step 1 |
| Step 3 無批次文字 | 回傳錯誤訊息 |
| 完整 chain | 三步驟資料正確傳遞 |

---

## 4. 測試命令與自動化

```bash
# 執行所有測試
uv run pytest tests/ -v

# 執行特定測試檔
uv run pytest tests/test_srt_generator.py -v

# 含 coverage 報告
uv run pytest tests/ --cov=src --cov=utils --cov-report=term-missing

# ruff 靜態檢查
uv run ruff check . --fix

# type 檢查（未來）
uv run mypy src/ --strict
```

### CI 配置建議（`.github/workflows/test.yml`）

```yaml
name: Test
on: [push, pull_request]
jobs:
  test:
    strategy:
      matrix:
        python-version: ["3.10", "3.11"]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv python install ${{ matrix.python-version }}
      - run: uv sync --group dev
      - run: uv run ruff check .
      - run: uv run pytest tests/ -v
```

---

## 5. 測試優先級排程

| 階段 | 工作項目 | 預計案例數 | 估計工時 |
|------|---------|-----------|---------|
| **Phase 1** 🔴 | T0-01 TTSEngine 測試 | 15 | 2h |
| | T0-02 ModelPool 測試 | 9 | 1h |
| | T0-03 ModelManager 測試 | 9 | 1h |
| | T2-01 test_config.py 修正 | 1 line | 5min |
| **Phase 2** 🟡 | T0-04 Monitor 測試 | 6 | 1h |
| | T1-01 to_gradio_audio 測試 | 6 | 30min |
| | T1-02 VoiceLibrary 獨立測試 | 6 | 30min |
| | T1-03 TTSServer 測試 | 6 | 1h |
| **Phase 3** 🟢 | TI-01 整合測試 | 3 | 1h |
| | TI-02 Workflow chain 測試 | 4 | 1h |
| | **總計** | **~64** | **~9h** |

---

## 6. 測試通過標準

- [ ] `uv run pytest tests/ -v` 全綠
- [ ] 所有 P0 測試案例通過
- [ ] 核心模組覆蓋率 ≥ 70%（tts_engine, multi_engine, audio_utils）
- [ ] `uv run ruff check .` 無 error
- [ ] Demo mode 啟動無 ERROR
