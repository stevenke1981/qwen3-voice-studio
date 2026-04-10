"""Qwen3 Voice Studio — SRT 資料結構（舊版相容）.

SRT 生成功能已遷移至 utils.srt_generator。
此模組僅保留 SRTEntry 資料類別以維持向下相容。
"""

from __future__ import annotations

from dataclasses import dataclass

from src.audio_utils import format_srt_time


@dataclass(frozen=True)
class SRTEntry:
    """SRT 字幕條目."""

    index: int
    start_time: float
    end_time: float
    text: str

    def to_srt(self) -> str:
        return (
            f"{self.index}\n"
            f"{format_srt_time(self.start_time)} --> {format_srt_time(self.end_time)}\n"
            f"{self.text}\n"
        )

