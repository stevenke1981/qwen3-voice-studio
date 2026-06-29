"""Qwen3 Voice Studio — 簡繁中文轉換工具.

使用 OpenCC 提供繁體 ↔ 簡體轉換功能。
適用於調整輸入文字字體以控制 TTS 輸出語言：
  - 繁體字 → 預設生成廣東話
  - 簡體字 → 預設生成中文（普通話）
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import opencc

logger = logging.getLogger(__name__)

# 延遲初始化 OpenCC，避免無痛匯入時載入 C 擴充
_converter_s2t = None
_converter_t2s = None


def _get_s2t() -> opencc.OpenCC:
    """取得簡 → 繁轉換器（單例）。"""
    global _converter_s2t
    if _converter_s2t is None:
        import opencc
        _converter_s2t = opencc.OpenCC("s2t.json")
    return _converter_s2t


def _get_t2s() -> opencc.OpenCC:
    """取得繁 → 簡轉換器（單例）。"""
    global _converter_t2s
    if _converter_t2s is None:
        import opencc
        _converter_t2s = opencc.OpenCC("t2s.json")
    return _converter_t2s


def to_traditional(text: str) -> str:
    """將簡體中文轉換為繁體中文。"""
    if not text:
        return text
    try:
        return _get_s2t().convert(text)
    except Exception as e:
        logger.warning("簡轉繁失敗: %s", e)
        return text


def to_simplified(text: str) -> str:
    """將繁體中文轉換為簡體中文。"""
    if not text:
        return text
    try:
        return _get_t2s().convert(text)
    except Exception as e:
        logger.warning("繁轉簡失敗: %s", e)
        return text
