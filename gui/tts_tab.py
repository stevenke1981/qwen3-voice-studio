"""
⚠️ DEPRECATED — 此模組已不再使用。

請改用 `gui/custom_voice_tab.py`（透過 ModelPool 操作）。
此檔案將在下一版本移除，保留僅供向後參考。

原因：
  - tts_tab.py 使用單一 TTSEngine，與現行 ModelPool 設計不一致。
  - custom_voice_tab.py 提供相同功能且整合 ModelPool + HistoryManager。
"""

from __future__ import annotations

import warnings

warnings.warn(
    "gui.tts_tab is deprecated. Use gui.custom_voice_tab instead.",
    DeprecationWarning,
    stacklevel=2,
)

# 以下保留原始實作供既有程式碼參考
# 所有新開發請使用 gui/custom_voice_tab.py
