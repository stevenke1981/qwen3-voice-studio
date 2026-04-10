"""Tests for src.srt_generator (SRT formatting only, no model needed)."""

from __future__ import annotations

from src.audio_utils import format_srt_time
from src.srt_generator import SRTEntry


class TestSRTEntry:
    def test_to_srt_format(self) -> None:
        entry = SRTEntry(index=1, start_time=0.0, end_time=1.5, text="你好世界")
        srt = entry.to_srt()
        lines = srt.strip().split("\n")
        assert lines[0] == "1"
        assert lines[1] == "00:00:00,000 --> 00:00:01,500"
        assert lines[2] == "你好世界"

    def test_multiple_entries(self) -> None:
        entries = [
            SRTEntry(index=1, start_time=0.0, end_time=1.0, text="First"),
            SRTEntry(index=2, start_time=1.0, end_time=2.5, text="Second"),
        ]
        result = "\n".join(e.to_srt() for e in entries)
        assert "1\n" in result
        assert "2\n" in result
        assert "First" in result
        assert "Second" in result


class TestSRTTimeFormatting:
    """SRT 時間戳格式化測試."""

    def test_boundaries(self) -> None:
        assert format_srt_time(0) == "00:00:00,000"
        assert format_srt_time(59.999) == "00:00:59,999"
        assert format_srt_time(60.0) == "00:01:00,000"
        assert format_srt_time(3600.0) == "01:00:00,000"

    def test_precision(self) -> None:
        result = format_srt_time(1.2345)
        assert result == "00:00:01,234"
