"""Qwen3 Voice Studio — i18n 多語言翻譯系統."""

from __future__ import annotations

from typing import Any

# ── 支援語言 ──────────────────────────────────────────────
SUPPORTED_LOCALES = ("zh-TW", "en")
DEFAULT_LOCALE = "zh-TW"

# ── 翻譯字典 ──────────────────────────────────────────────
_TRANSLATIONS: dict[str, dict[str, str]] = {
    # ── 通用 ──
    "app_title": {"zh-TW": "Qwen3 Voice Studio", "en": "Qwen3 Voice Studio"},
    "app_subtitle": {
        "zh-TW": "專業文字轉語音工作室 — 純 TTS + SRT 字幕",
        "en": "Professional Text-to-Speech Studio — TTS + SRT Subtitles",
    },
    "language_label": {"zh-TW": "介面語言", "en": "Language"},
    # ── Tab 標題 ──
    "tab_tts": {"zh-TW": "📝 文章轉語音", "en": "📝 Text to Speech"},
    "tab_voice": {"zh-TW": "🎨 聲音工坊", "en": "🎨 Voice Workshop"},
    "tab_batch": {"zh-TW": "📦 批量處理", "en": "📦 Batch Processing"},
    "tab_history": {"zh-TW": "📚 歷史記錄", "en": "📚 History"},
    "tab_monitor": {"zh-TW": "📊 效能監控", "en": "📊 Performance"},
    "tab_settings": {"zh-TW": "⚙️ 設定", "en": "⚙️ Settings"},
    # ── TTS Tab ──
    "input_text": {"zh-TW": "輸入文字", "en": "Input Text"},
    "input_placeholder": {
        "zh-TW": "在此輸入要轉換為語音的文章...",
        "en": "Enter text to convert to speech...",
    },
    "upload_file": {"zh-TW": "上傳檔案 (.txt / .md)", "en": "Upload File (.txt / .md)"},
    "speaker": {"zh-TW": "說話者", "en": "Speaker"},
    "language_detect": {"zh-TW": "語言（自動偵測）", "en": "Language (Auto Detect)"},
    "srt_mode": {"zh-TW": "SRT 粒度", "en": "SRT Granularity"},
    "srt_sentence": {"zh-TW": "句子級別", "en": "Sentence Level"},
    "srt_word": {"zh-TW": "詞語級別", "en": "Word Level"},
    "btn_convert": {"zh-TW": "🚀 一鍵轉換", "en": "🚀 Convert"},
    "btn_stop": {"zh-TW": "⏹️ 停止", "en": "⏹️ Stop"},
    "output_audio": {"zh-TW": "生成語音", "en": "Generated Audio"},
    "output_srt": {"zh-TW": "SRT 字幕預覽", "en": "SRT Subtitle Preview"},
    "btn_download_audio": {"zh-TW": "下載音訊", "en": "Download Audio"},
    "btn_download_srt": {"zh-TW": "下載 SRT", "en": "Download SRT"},
    "waveform": {"zh-TW": "波形圖", "en": "Waveform"},
    # ── 情緒 / 風格控制 ──
    "style_controls": {"zh-TW": "情緒 / 風格控制", "en": "Emotion / Style Controls"},
    "pitch": {"zh-TW": "音高", "en": "Pitch"},
    "speed": {"zh-TW": "語速", "en": "Speed"},
    "energy": {"zh-TW": "能量", "en": "Energy"},
    "volume": {"zh-TW": "音量", "en": "Volume"},
    "emotion": {"zh-TW": "情緒", "en": "Emotion"},
    "emotion_neutral": {"zh-TW": "中性", "en": "Neutral"},
    "emotion_happy": {"zh-TW": "開心", "en": "Happy"},
    "emotion_sad": {"zh-TW": "悲傷", "en": "Sad"},
    "emotion_angry": {"zh-TW": "憤怒", "en": "Angry"},
    "emotion_gentle": {"zh-TW": "溫柔", "en": "Gentle"},
    # ── Voice Workshop ──
    "voice_library": {"zh-TW": "聲音圖書館", "en": "Voice Library"},
    "voice_design": {"zh-TW": "語音設計", "en": "Voice Design"},
    "voice_clone": {"zh-TW": "語音克隆", "en": "Voice Clone"},
    "voice_desc": {
        "zh-TW": "用文字描述想要的聲音風格...",
        "en": "Describe the voice style you want...",
    },
    "voice_desc_label": {"zh-TW": "聲音描述", "en": "Voice Description"},
    "ref_audio": {"zh-TW": "參考音檔", "en": "Reference Audio"},
    "ref_text": {"zh-TW": "參考文字（選填）", "en": "Reference Text (Optional)"},
    "btn_design": {"zh-TW": "🎨 設計音色", "en": "🎨 Design Voice"},
    "btn_clone": {"zh-TW": "🔄 克隆音色", "en": "🔄 Clone Voice"},
    "btn_save_voice": {"zh-TW": "💾 儲存音色", "en": "💾 Save Voice"},
    "btn_load_voice": {"zh-TW": "📂 載入音色", "en": "📂 Load Voice"},
    "btn_delete_voice": {"zh-TW": "🗑️ 刪除音色", "en": "🗑️ Delete Voice"},
    "voice_name": {"zh-TW": "音色名稱", "en": "Voice Name"},
    "saved_voices": {"zh-TW": "已儲存音色", "en": "Saved Voices"},
    "multi_speaker_compare": {"zh-TW": "多說話者比較", "en": "Multi-Speaker Compare"},
    "btn_compare": {"zh-TW": "🔊 比較", "en": "🔊 Compare"},
    "select_speakers": {"zh-TW": "選擇說話者（多選）", "en": "Select Speakers (Multi)"},
    "compare_text": {"zh-TW": "比較用文字", "en": "Comparison Text"},
    # ── Batch ──
    "batch_upload": {"zh-TW": "上傳多個檔案", "en": "Upload Multiple Files"},
    "batch_output_dir": {"zh-TW": "輸出資料夾", "en": "Output Directory"},
    "btn_batch_convert": {"zh-TW": "📦 批量轉換", "en": "📦 Batch Convert"},
    "batch_progress": {"zh-TW": "進度", "en": "Progress"},
    "batch_include_srt": {"zh-TW": "同時產生 SRT", "en": "Include SRT"},
    "btn_export_zip": {"zh-TW": "📥 匯出 ZIP", "en": "📥 Export ZIP"},
    # ── History ──
    "history_search": {"zh-TW": "搜尋歷史...", "en": "Search history..."},
    "history_table": {"zh-TW": "歷史記錄", "en": "History Records"},
    "history_date": {"zh-TW": "日期", "en": "Date"},
    "history_text_preview": {"zh-TW": "文字預覽", "en": "Text Preview"},
    "history_speaker_col": {"zh-TW": "說話者", "en": "Speaker"},
    "history_duration": {"zh-TW": "時長", "en": "Duration"},
    "btn_replay": {"zh-TW": "🔁 重播", "en": "🔁 Replay"},
    "btn_download_history_srt": {
        "zh-TW": "📥 下載 SRT",
        "en": "📥 Download SRT",
    },
    "btn_clear_history": {"zh-TW": "🗑️ 清除歷史", "en": "🗑️ Clear History"},
    # ── Monitor ──
    "gpu_usage": {"zh-TW": "GPU 使用率", "en": "GPU Usage"},
    "gpu_memory": {"zh-TW": "GPU 記憶體", "en": "GPU Memory"},
    "latency": {"zh-TW": "延遲 (ms)", "en": "Latency (ms)"},
    "cpu_usage": {"zh-TW": "CPU 使用率", "en": "CPU Usage"},
    "ram_usage": {"zh-TW": "RAM 使用量", "en": "RAM Usage"},
    "model_loaded": {"zh-TW": "模型已載入", "en": "Model Loaded"},
    "model_not_loaded": {"zh-TW": "模型未載入", "en": "Model Not Loaded"},
    "btn_refresh_metrics": {"zh-TW": "🔄 重新整理", "en": "🔄 Refresh"},
    # ── Settings ──
    "settings_tts": {"zh-TW": "TTS 設定", "en": "TTS Settings"},
    "model_path": {"zh-TW": "模型路徑", "en": "Model Path"},
    "device": {"zh-TW": "裝置", "en": "Device"},
    "port": {"zh-TW": "伺服器埠號", "en": "Server Port"},
    "auto_start": {"zh-TW": "自動啟動伺服器", "en": "Auto Start Server"},
    "api_key": {"zh-TW": "API Key（雲端模式）", "en": "API Key (Cloud Mode)"},
    "use_cloud": {"zh-TW": "使用雲端 API", "en": "Use Cloud API"},
    "btn_save_settings": {"zh-TW": "💾 儲存設定", "en": "💾 Save Settings"},
    "btn_start_server": {"zh-TW": "▶️ 啟動伺服器", "en": "▶️ Start Server"},
    "btn_stop_server": {"zh-TW": "⏹️ 停止伺服器", "en": "⏹️ Stop Server"},
    "server_status": {"zh-TW": "伺服器狀態", "en": "Server Status"},
    "server_running": {"zh-TW": "🟢 運行中", "en": "🟢 Running"},
    "server_stopped": {"zh-TW": "🔴 已停止", "en": "🔴 Stopped"},
    # ── TTS Tab（元件鍵） ──
    "tts_input_text": {"zh-TW": "輸入文字", "en": "Input Text"},
    "tts_placeholder": {"zh-TW": "在此輸入要轉換為語音的文字...", "en": "Enter text to convert to speech..."},
    "tts_speaker": {"zh-TW": "說話者", "en": "Speaker"},
    "tts_language": {"zh-TW": "語言", "en": "Language"},
    "tts_instruct": {"zh-TW": "指令（選填）", "en": "Instruction (Optional)"},
    "tts_instruct_placeholder": {"zh-TW": "例如：用溫柔的語氣朗讀", "en": "e.g.: Read in a gentle tone"},
    "tts_srt_mode": {"zh-TW": "SRT 字幕粒度", "en": "SRT Granularity"},
    "tts_synthesize": {"zh-TW": "🚀 開始合成", "en": "🚀 Synthesize"},
    "tts_audio_output": {"zh-TW": "合成語音", "en": "Generated Audio"},
    "tts_srt_output": {"zh-TW": "SRT 字幕預覽", "en": "SRT Preview"},
    "tts_status": {"zh-TW": "狀態", "en": "Status"},
    "status_synthesis_done": {
        "zh-TW": "✅ 合成完成！時長：{duration}s，延遲：{latency}ms",
        "en": "✅ Done! Duration: {duration}s, Latency: {latency}ms",
    },
    "error_empty_text": {"zh-TW": "請輸入文字", "en": "Please enter text"},
    "error_model_not_loaded": {"zh-TW": "模型尚未載入", "en": "Model not loaded"},
    # ── Batch Tab ──
    "batch_description": {
        "zh-TW": "上傳文字檔批量合成語音，並自動產生 SRT 字幕。",
        "en": "Upload text files for batch speech synthesis with automatic SRT subtitle generation.",
    },
    "batch_start": {"zh-TW": "📦 開始批量合成", "en": "📦 Start Batch"},
    "batch_status": {"zh-TW": "批量處理狀態", "en": "Batch Status"},
    "batch_output": {"zh-TW": "輸出檔案", "en": "Output Files"},
    "batch_no_file": {"zh-TW": "請上傳檔案", "en": "Please upload a file"},
    "batch_empty_file": {"zh-TW": "檔案內容為空", "en": "File content is empty"},
    "batch_done": {
        "zh-TW": "✅ 批量完成！共 {count} 段，儲存至：{path}",
        "en": "✅ Batch done! {count} segments saved to: {path}",
    },
    # ── History Tab ──
    "history_search_placeholder": {"zh-TW": "輸入關鍵字搜尋...", "en": "Enter keyword to search..."},
    "history_search_btn": {"zh-TW": "🔍 搜尋", "en": "🔍 Search"},
    "history_refresh": {"zh-TW": "🔄 重新整理", "en": "🔄 Refresh"},
    "history_clear": {"zh-TW": "🗑️ 清除歷史", "en": "🗑️ Clear History"},
    "history_id": {"zh-TW": "ID", "en": "ID"},
    "history_time": {"zh-TW": "時間", "en": "Time"},
    "history_text": {"zh-TW": "文字預覽", "en": "Text Preview"},
    "history_cleared": {"zh-TW": "歷史記錄已清除", "en": "History cleared"},
    # ── Voice Workshop ──
    "voice_pitch": {"zh-TW": "音高", "en": "Pitch"},
    "voice_speed": {"zh-TW": "語速", "en": "Speed"},
    "voice_energy": {"zh-TW": "能量", "en": "Energy"},
    "voice_save": {"zh-TW": "💾 儲存音色", "en": "💾 Save Voice"},
    "voice_refresh": {"zh-TW": "🔄 重新整理", "en": "🔄 Refresh"},
    "voice_delete": {"zh-TW": "🗑️ 刪除", "en": "🗑️ Delete"},
    "voice_delete_name": {"zh-TW": "要刪除的音色名稱", "en": "Voice Name to Delete"},
    "voice_saved": {"zh-TW": "✅ 音色「{name}」已儲存", "en": "✅ Voice '{name}' saved"},
    "voice_deleted": {"zh-TW": "✅ 音色「{name}」已刪除", "en": "✅ Voice '{name}' deleted"},
    "voice_design_desc": {
        "zh-TW": "用文字描述想要的聲音風格，AI 將自動產生對應音色。",
        "en": "Describe your desired voice style, and AI will generate it automatically.",
    },
    "voice_design_description": {"zh-TW": "聲音描述", "en": "Voice Description"},
    "voice_design_placeholder": {
        "zh-TW": "例如：年輕女性，溫柔輕快，帶有微笑感",
        "en": "e.g.: Young female, gentle and lively, with a smile",
    },
    "voice_design_generate": {"zh-TW": "🎨 生成音色", "en": "🎨 Generate Voice"},
    "voice_design_done": {"zh-TW": "✅ 音色設計完成", "en": "✅ Voice design complete"},
    "voice_clone_desc": {
        "zh-TW": "上傳參考音檔，AI 將克隆該聲音合成新內容。",
        "en": "Upload a reference audio file, and AI will clone that voice to synthesize new content.",
    },
    "voice_clone_ref": {"zh-TW": "參考音檔", "en": "Reference Audio"},
    "voice_clone_generate": {"zh-TW": "🔄 克隆合成", "en": "🔄 Clone & Synthesize"},
    "voice_clone_done": {"zh-TW": "✅ 語音克隆完成", "en": "✅ Voice clone complete"},
    "error_voice_lib_unavailable": {"zh-TW": "聲音圖書館不可用", "en": "Voice library unavailable"},
    "error_empty_name": {"zh-TW": "請輸入音色名稱", "en": "Please enter a voice name"},
    "error_no_ref_audio": {"zh-TW": "請上傳參考音檔", "en": "Please upload a reference audio"},
    "error_invalid_audio": {"zh-TW": "無效的音訊格式", "en": "Invalid audio format"},
    # ── Settings Tab ──
    "settings_title": {"zh-TW": "應用程式設定", "en": "Application Settings"},
    "settings_model_path": {"zh-TW": "TTS 模型路徑", "en": "TTS Model Path"},
    "settings_srt_mode": {"zh-TW": "SRT 時間分配模式", "en": "SRT Timing Mode"},
    "settings_zh_cpm": {"zh-TW": "中文朗讀速率（字/分鐘）", "en": "Chinese CPM"},
    "settings_en_wpm": {"zh-TW": "英文朗讀速率（字/分鐘）", "en": "English WPM"},
    "settings_output_dir": {"zh-TW": "音訊輸出目錄", "en": "Audio Output Directory"},
    "settings_device": {"zh-TW": "運算裝置", "en": "Device"},
    "settings_port": {"zh-TW": "伺服器埠號", "en": "Server Port"},
    "settings_auto_start": {"zh-TW": "自動啟動伺服器", "en": "Auto-start Server"},
    "settings_save": {"zh-TW": "💾 儲存設定", "en": "💾 Save Settings"},
    "settings_saved": {"zh-TW": "✅ 設定已儲存", "en": "✅ Settings saved"},
    # ── Monitor Tab ──
    "monitor_title": {"zh-TW": "系統效能指標", "en": "System Performance Metrics"},
    "monitor_refresh": {"zh-TW": "🔄 重新整理", "en": "🔄 Refresh"},
    # ── Error Panel ──
    "tab_errors": {"zh-TW": "❗ 錯誤日誌", "en": "❗ Error Log"},
    "error_log_title": {"zh-TW": "錯誤記錄", "en": "Error Log"},
    "error_refresh": {"zh-TW": "🔄 重新整理", "en": "🔄 Refresh"},
    "error_export": {"zh-TW": "📥 匯出 CSV", "en": "📥 Export CSV"},
    "error_clear": {"zh-TW": "🗑️ 清除", "en": "🗑️ Clear"},
    "error_exported": {"zh-TW": "✅ 已匯出至：{path}", "en": "✅ Exported to: {path}"},
    "error_panel": {"zh-TW": "錯誤訊息", "en": "Error Messages"},
    "btn_copy_error": {"zh-TW": "📋 一鍵複製", "en": "📋 Copy All"},
    "btn_export_log": {"zh-TW": "📥 匯出日誌", "en": "📥 Export Logs"},
    "btn_clear_errors": {"zh-TW": "🗑️ 清除", "en": "🗑️ Clear"},
    "no_errors": {"zh-TW": "目前沒有錯誤", "en": "No errors"},
    # ── 狀態訊息 ──
    "status_ready": {"zh-TW": "就緒", "en": "Ready"},
    "status_converting": {"zh-TW": "轉換中...", "en": "Converting..."},
    "status_done": {"zh-TW": "完成！", "en": "Done!"},
    "status_error": {"zh-TW": "錯誤", "en": "Error"},
    "status_downloading": {"zh-TW": "正在下載模型...", "en": "Downloading model..."},
    "status_loading": {"zh-TW": "正在載入模型...", "en": "Loading model..."},
    "status_generating_srt": {"zh-TW": "正在產生 SRT 字幕...", "en": "Generating SRT..."},
    # ── 模型管理 ──
    "model_auto_download": {
        "zh-TW": "首次啟動將自動下載模型（約 1.5 GB）",
        "en": "Models will be auto-downloaded on first launch (~1.5 GB)",
    },
    "model_download_complete": {
        "zh-TW": "模型下載完成",
        "en": "Model download complete",
    },
    # ── Validation ──
    "err_no_text": {"zh-TW": "請輸入文字", "en": "Please enter text"},
    "err_no_speaker": {"zh-TW": "請選擇說話者", "en": "Please select a speaker"},
    "err_server_not_running": {
        "zh-TW": "TTS 伺服器未啟動",
        "en": "TTS server is not running",
    },
    "err_model_not_loaded": {
        "zh-TW": "模型尚未載入",
        "en": "Model not loaded yet",
    },
    "err_file_too_large": {
        "zh-TW": "檔案過大（上限 10 MB）",
        "en": "File too large (max 10 MB)",
    },
    "err_unsupported_format": {
        "zh-TW": "不支援的檔案格式",
        "en": "Unsupported file format",
    },
    "err_conversion_failed": {
        "zh-TW": "轉換失敗",
        "en": "Conversion failed",
    },
    "err_srt_failed": {
        "zh-TW": "SRT 生成失敗",
        "en": "SRT generation failed",
    },
}


def t(key: str, locale: str = DEFAULT_LOCALE, **kwargs: Any) -> str:
    """取得翻譯文字.

    Args:
        key: 翻譯鍵值
        locale: 語言代碼 (zh-TW / en)
        **kwargs: 格式化參數

    Returns:
        翻譯後的字串，若找不到則回傳 key
    """
    entry = _TRANSLATIONS.get(key)
    if entry is None:
        return key
    text = entry.get(locale, entry.get(DEFAULT_LOCALE, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


def get_all_keys() -> list[str]:
    """取得所有翻譯鍵值."""
    return list(_TRANSLATIONS.keys())


def get_translations_for_locale(locale: str) -> dict[str, str]:
    """取得指定語言的所有翻譯."""
    return {key: t(key, locale) for key in _TRANSLATIONS}


def add_translation(key: str, translations: dict[str, str]) -> None:
    """新增或更新翻譯項目."""
    _TRANSLATIONS[key] = {**_TRANSLATIONS.get(key, {}), **translations}
