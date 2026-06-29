"""
⚠️ DEPRECATED — 此模組已不再使用。

請改用 `gui/voice_design_tab.py` 和 `gui/voice_clone_tab.py`。
此檔案將在下一版本移除，保留僅供向後參考。

原因：
  - voice_tab.py 使用單一 TTSEngine，與現行 ModelPool 設計不一致。
  - voice_design_tab.py 和 voice_clone_tab.py 各自獨立且整合 ModelPool。
"""

from __future__ import annotations

import warnings

warnings.warn(
    "gui.voice_tab is deprecated. Use gui.voice_design_tab / gui.voice_clone_tab instead.",
    DeprecationWarning,
    stacklevel=2,
)

# 以下保留原始實作供既有程式碼參考
# 所有新開發請使用 gui/voice_design_tab.py 或 gui/voice_clone_tab.py
