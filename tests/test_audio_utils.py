"""Tests for src.audio_utils module."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.audio_utils import format_srt_time, read_text_file, split_text_to_sentences


class TestFormatSrtTime:
    def test_zero(self) -> None:
        assert format_srt_time(0.0) == "00:00:00,000"

    def test_one_second(self) -> None:
        assert format_srt_time(1.0) == "00:00:01,000"

    def test_complex_time(self) -> None:
        result = format_srt_time(3661.5)
        assert result == "01:01:01,500"

    def test_milliseconds(self) -> None:
        result = format_srt_time(0.123)
        assert result == "00:00:00,123"

    def test_negative_clamps_to_zero(self) -> None:
        result = format_srt_time(-1.0)
        assert result == "00:00:00,000"


class TestSplitTextToSentences:
    def test_chinese_sentences(self) -> None:
        text = "你好。世界！再見？"
        result = split_text_to_sentences(text)
        assert len(result) == 3

    def test_english_sentences(self) -> None:
        text = "Hello. World! Goodbye?"
        result = split_text_to_sentences(text)
        assert len(result) == 3

    def test_mixed_sentences(self) -> None:
        text = "你好。Hello world!"
        result = split_text_to_sentences(text)
        assert len(result) == 2

    def test_empty_text(self) -> None:
        result = split_text_to_sentences("")
        assert result == []

    def test_newline_split(self) -> None:
        text = "第一行\n第二行\n第三行"
        result = split_text_to_sentences(text)
        assert len(result) == 3


class TestReadTextFile:
    def test_read_utf8(self, sample_text_file: Path) -> None:
        content = read_text_file(str(sample_text_file))
        assert "第一句話" in content

    def test_nonexistent_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            read_text_file("/nonexistent/path/file.txt")

    def test_too_large_file(self, tmp_path: Path) -> None:
        big_file = tmp_path / "big.txt"
        big_file.write_text("x" * (11 * 1024 * 1024))
        with pytest.raises(ValueError, match="10 MB"):
            read_text_file(str(big_file))
