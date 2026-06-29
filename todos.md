# qwen3-voice-studio — 優化改善任務清單

> 產生日期：2026-06-29
> 來源：CBM 全專案架構分析 (47 檔案, 266 符號, 916 邊)

---

## 🔴 P0 — 重大問題（必須優先處理）

### [P0-01] 清理死程式碼（未使用的模組）

| 檔案 | 狀態 | 說明 |
|------|------|------|
| `gui/tts_tab.py` | 未使用 | 內含 `build_tts_tab()`，但 `app_ui.py` 未匯入也未呼叫。與 `custom_voice_tab.py` 高度重複。 |
| `gui/voice_tab.py` | 未使用 | 內含 `build_voice_tab()`，但 `app_ui.py` 未匯入。已被 `voice_design_tab.py` + `voice_clone_tab.py` + `custom_voice_tab.py` 取代。 |
| `src/srt_generator.py` | 幾乎無用 | 僅保留 `SRTEntry` dataclass（向後相容）。實際 SRT 實作已遷移至 `utils/srt_generator.py`。 |

**驗收標準：**
- [ ] `gui/tts_tab.py` 刪除或標註 deprecated
- [ ] `gui/voice_tab.py` 刪除或標註 deprecated
- [ ] `src/srt_generator.py` 縮減為僅匯出 `SRTEntry`（或直接刪除並更新 import）

### [P0-02] 重複實作 — 兩個 `format_srt_time` / `format_srt_timestamp`

| 位置 | 函式名稱 |
|------|---------|
| `src/audio_utils.py` | `format_srt_time(seconds)` → 回傳 `HH:MM:SS,mmm` |
| `utils/srt_generator.py` | `format_srt_timestamp(seconds)` → 回傳 `HH:MM:SS,mmm` |

兩者邏輯完全相同，但實作細節不同（前者手動計算，後者用 `divmod`）。應統一為一個來源。

**驗收標準：**
- [ ] 擇一保留，另一者委派（delegate）
- [ ] 所有 import 指向同一實作

### [P0-03] 測試 `model_path` 屬性不存在

`tests/test_config.py::TestTTSSettings::test_defaults` 第 13 行：
```python
assert s.model_path == "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
```
但 `TTSSettings` 的欄位名為 `base_model`，不是 `model_path`。此測試必定失敗。

**驗收標準：**
- [ ] 修正為 `s.base_model`
- [ ] `uv run pytest tests/test_config.py -v` 通過

### [P0-04] 埠號不一致

| 位置 | 值 |
|------|-----|
| `src/config.py` `DEFAULT_PORT` | `8990` |
| `app.py` `parse_args()` | `--port` 預設 `7860` |

`DEFAULT_PORT = 8990` 僅在 `TTSSettings.port` 使用，但 `app.py` 的 `--port` 預設是 `7860`。兩者不一致。

**驗收標準：**
- [ ] 統一埠號（建議 `7860` 為預設，因為 Gradio 慣例）

---

## 🟡 P1 — 架構與品質改善

### [P1-01] 核心引擎無單元測試

| 模組 | 測試覆蓋率 |
|------|-----------|
| `src/tts_engine.py` | ❌ 0% |
| `src/multi_engine.py` | ❌ 0% |
| `src/model_manager.py` | ❌ 0% |
| `src/monitor.py` | ❌ 0% |
| `src/tts_server.py` | ❌ 0% |
| `src/voice_library.py` | ⚠️ 與 error_handler 共用測試檔 |
| `src/audio_utils.py` | ✅ `to_gradio_audio()` 未測試 |

**驗收標準：**
- [ ] `src/tts_engine.py` 新增 `TTSResult` dataclass 與 demo mode 測試
- [ ] `src/multi_engine.py` 新增 `ModelPool` 測試（mock TTSEngine）
- [ ] `src/monitor.py` 新增 `get_system_metrics` 與 `format_metrics_display` 測試
- [ ] `src/audio_utils.py` 新增 `to_gradio_audio()` 測試（含全零邊界）
- [ ] `src/voice_library.py` 移至獨立測試檔

### [P1-02] ModelPool 下載錯誤被靜默忽略

```python
def _ensure_downloaded(self, model_path: str) -> None:
    try:
        ensure_tts_model_available(model_path)
    except Exception as e:
        logger.warning("模型下載失敗（將嘗試從快取載入）: %s", e)
```

下載失敗只 log warning 不拋出，如果模型不存在於快取，後續 `engine.load_model()` 會以不明確的方式失敗。

**驗收標準：**
- [ ] 明確區分「下載失敗但快取存在」與「模型完全不可用」
- [ ] 後者應拋出具體異常

### [P1-03] `monitor.py` nvmlInit/nvmlShutdown 每次呼叫重新初始化

```python
def get_system_metrics(...):
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    ...
    pynvml.nvmlShutdown()
```

每次呼叫都 init/shutdown NVML，約增加 50-100ms 延遲，且非執行緒安全。

**驗收標準：**
- [ ] 改為模組層級惰性初始化（lazy-init singleton pattern）
- [ ] 或使用 `nvmlInit()` 只呼叫一次

### [P1-04] `settings_tab.py` 儲存後未更新記憶體中的 settings 物件

`_save()` 建立新的 `AppSettings` 並寫入檔案，但 `build_settings_tab()` 接收的 `settings` 參數未被更新。使用者必須重啟才能看到變更生效。

**驗收標準：**
- [ ] `save_btn.click` 回呼應更新傳入的 `settings` 物件
- [ ] 或提供即時 apply 機制

### [P1-05] `pyproject.toml` `qwen-tts` 未鎖定版本

當前只有 `qwen-tts`（無版本），但 spec 寫明 `0.1.1`。應明確鎖定以免意外升級中斷相容性。

**驗收標準：**
- [ ] `qwen-tts = "0.1.1"` 明確鎖定

### [P1-06] ErrorHandler 不一致的可變/不可變模式

```python
def add_error(self, message, detail="", level="ERROR"):
    new_records = [*self._records, record]  # 建立新 list（immutable-style）
    ...
    self._records = new_records
```

`_records` 是 `list[ErrorRecord]`（可變），但 `add_error` 卻用複製方式。要嘛全部不可變（tuple），要嘛直接 `append`。

**驗收標準：**
- [ ] 統一律定：`list.append()` 或 `tuple` + 重新指派

### [P1-07] `workflow_tab.py` 重複 import `soundfile`

在第 51、91、136、152 行重複 `import soundfile as sf`。應拉到檔案頂端。

**驗收標準：**
- [ ] `import soundfile as sf` 拉到模組層級

---

## 🟢 P2 — 程式碼衛生

### [P2-01] `build_app()` 使用 `Any` 型別

```python
def build_app(
    model_pool: ModelPool | None = None,
    ...
    settings: Any = None,  # ← 應為 AppSettings
)
```

**驗收標準：**
- [ ] `settings: AppSettings | None = None`

### [P2-02] GUI tab build 函式型別未使用 TYPE_CHECKING

`build_workflow_tab`、`build_voice_design_tab` 等的 `error_handler` 參數在執行時期型別為 `ErrorHandler` 但宣告為 `Any`。

**驗收標準：**
- [ ] 執行時期參數使用正確型別而非 `Any`

### [P2-03] `youtube_tab.py` 路徑穿越風險

`_sanitize_filename()` 允許底線和空白，但未處理 `..\\` 或絕對路徑 prefix。`_delete_template()` 直接 `Path(template_path).unlink()`。

**驗收標準：**
- [ ] `_sanitize_filename` 拒絕包含 `..`、`/`、`\\` 的名稱
- [ ] `_delete_template` 限制路徑在 `wav-template/` 目錄下

### [P2-04] `.opencode/status-footer/` 未加入 `.gitignore`

**驗收標準：**
- [ ] 在 `.gitignore` 中加上 `.opencode/`

---

## 🔵 P3 — 可選增強

### [P3-01] 新增 CI 配置（GitHub Actions）

- `ruff check` + `pytest` 自動執行
- Python 3.10 / 3.11 矩陣測試

### [P3-02] 語意化版本號導入

當前版本 `1.0.0` 但仍是開發早期。導入 `__version__` 字串。

### [P3-03] `uv.lock` 提交至版本控制

確保可重現安裝。

---

## 總體統計

| 優先級 | 數量 |
|--------|------|
| 🔴 P0 | 4 |
| 🟡 P1 | 7 |
| 🟢 P2 | 4 |
| 🔵 P3 | 3 |
| **總計** | **18** |

## 進行方式建議

1. **第一階段（P0）**：修正死程式碼、重複實作、錯誤測試、埠號不一致
2. **第二階段（P1）**：補測試、ModelPool 錯誤處理、NVML 最佳化、設定同步
3. **第三階段（P2）**：型別清理、安全性、gitignore
4. **第四階段（P3）**：CI、版本號、lockfile
