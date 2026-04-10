"""Tests for utils.srt_generator — 純句子級 SRT 生成器（無需模型）."""

from __future__ import annotations

import pytest

from utils.srt_generator import (
    allocate_rate_based_durations,
    allocate_uniform_durations,
    build_srt_string,
    format_srt_timestamp,
    generate_srt,
    normalize_text,
    split_sentences,
    write_srt,
)

# ---------------------------------------------------------------------------
# normalize_text
# ---------------------------------------------------------------------------


class TestNormalizeText:
    def test_empty(self) -> None:
        assert normalize_text("") == ""

    def test_strips_whitespace(self) -> None:
        assert normalize_text("  hello  ") == "hello"

    def test_collapses_spaces(self) -> None:
        assert normalize_text("a   b\t\tc") == "a b c"

    def test_removes_zero_width(self) -> None:
        text = "你\u200b好"
        assert normalize_text(text) == "你好"

    def test_normalizes_ellipsis(self) -> None:
        assert normalize_text("等等……再說") == "等等…再說"
        assert normalize_text("etc...end") == "etc…end"

    def test_preserves_newlines(self) -> None:
        text = "第一行\n第二行"
        result = normalize_text(text)
        assert "\n" in result
        assert "第一行" in result
        assert "第二行" in result


# ---------------------------------------------------------------------------
# split_sentences
# ---------------------------------------------------------------------------


class TestSplitSentences:
    def test_empty(self) -> None:
        assert split_sentences("") == []

    def test_single_sentence_no_punct(self) -> None:
        result = split_sentences("Hello world")
        assert result == ["Hello world"]

    def test_chinese_primary_punct(self) -> None:
        text = "你好世界。這是測試！結束了？"
        result = split_sentences(text)
        assert len(result) == 3
        assert result[0].endswith("。")
        assert result[1].endswith("！")
        assert result[2].endswith("？")

    def test_english_primary_punct(self) -> None:
        text = "Hello world. This is a test! Done?"
        result = split_sentences(text)
        assert len(result) == 3

    def test_secondary_split_long_sentence(self) -> None:
        # 超過 max_length=20 的句子應被次要標點切分
        long = "一，二，三，四，五，六，七，八，九，十，十一，十二，十三，"
        result = split_sentences(long, secondary_split=True, max_length=20)
        assert len(result) > 1

    def test_secondary_split_disabled(self) -> None:
        long = "一，二，三，四，五，六，七，八，九，十，十一，十二，十三，"
        result = split_sentences(long, secondary_split=False)
        assert len(result) == 1

    def test_paragraph_separation(self) -> None:
        text = "第一段。\n\n第二段。"
        result = split_sentences(text)
        assert len(result) == 2

    def test_mixed_language(self) -> None:
        text = "Hello! 你好。Goodbye?"
        result = split_sentences(text)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# allocate_uniform_durations
# ---------------------------------------------------------------------------


class TestAllocateUniformDurations:
    def test_empty(self) -> None:
        assert allocate_uniform_durations([], 10.0) == []

    def test_zero_duration(self) -> None:
        result = allocate_uniform_durations(["a", "b"], 0.0)
        assert result == [0.0, 0.0]

    def test_negative_duration(self) -> None:
        result = allocate_uniform_durations(["a"], -1.0)
        assert result == [0.0]

    def test_single_sentence(self) -> None:
        result = allocate_uniform_durations(["abc"], 5.0)
        assert result == [5.0]

    def test_total_preserved(self) -> None:
        sents = ["a", "b", "c"]
        total = 10.0
        result = allocate_uniform_durations(sents, total)
        assert abs(sum(result) - total) < 1e-9

    def test_uniform_distribution(self) -> None:
        sents = ["a", "b", "c", "d"]
        result = allocate_uniform_durations(sents, 8.0)
        assert all(abs(d - 2.0) < 1e-9 for d in result)

    def test_floating_point_correction(self) -> None:
        sents = ["a"] * 3
        result = allocate_uniform_durations(sents, 1.0)
        assert abs(sum(result) - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# allocate_rate_based_durations
# ---------------------------------------------------------------------------


class TestAllocateRateBasedDurations:
    def test_empty(self) -> None:
        assert allocate_rate_based_durations([], 10.0) == []

    def test_zero_duration(self) -> None:
        result = allocate_rate_based_durations(["你好", "世界"], 0.0)
        assert result == [0.0, 0.0]

    def test_total_preserved(self) -> None:
        sents = ["你好世界", "This is English", "混合 mixed 中文"]
        total = 12.345
        result = allocate_rate_based_durations(sents, total)
        assert abs(sum(result) - total) < 1e-9

    def test_longer_sentence_gets_more_time(self) -> None:
        short = "好。"
        long = "這是一個比較長的中文句子，包含很多字。"
        result = allocate_rate_based_durations([short, long], 10.0)
        assert result[1] > result[0]

    def test_fallback_for_unknown_chars(self) -> None:
        # 數字與標點沒有中英文字元
        result = allocate_rate_based_durations(["123", "456789"], 6.0)
        assert abs(sum(result) - 6.0) < 1e-9
        # 較長者時間應較多
        assert result[1] > result[0]

    def test_custom_rates(self) -> None:
        sents = ["你好世界", "Hello world"]
        r1 = allocate_rate_based_durations(sents, 10.0, zh_cpm=80, en_wpm=150)
        r2 = allocate_rate_based_durations(sents, 10.0, zh_cpm=160, en_wpm=150)
        # 降低中文速率 → 中文句子佔比增加
        assert r1[0] > r2[0]


# ---------------------------------------------------------------------------
# format_srt_timestamp
# ---------------------------------------------------------------------------


class TestFormatSRTTimestamp:
    def test_zero(self) -> None:
        assert format_srt_timestamp(0.0) == "00:00:00,000"

    def test_one_second(self) -> None:
        assert format_srt_timestamp(1.0) == "00:00:01,000"

    def test_milliseconds(self) -> None:
        assert format_srt_timestamp(1.5) == "00:00:01,500"

    def test_one_minute(self) -> None:
        assert format_srt_timestamp(60.0) == "00:01:00,000"

    def test_one_hour(self) -> None:
        assert format_srt_timestamp(3600.0) == "01:00:00,000"

    def test_complex(self) -> None:
        # 1h 23m 45.678s
        t = 3600 + 23 * 60 + 45.678
        assert format_srt_timestamp(t) == "01:23:45,678"

    def test_negative_clamped(self) -> None:
        assert format_srt_timestamp(-1.0) == "00:00:00,000"

    def test_rounding(self) -> None:
        # 1.0005 → 1ms 四捨五入
        result = format_srt_timestamp(1.0005)
        assert result.startswith("00:00:01,")


# ---------------------------------------------------------------------------
# build_srt_string
# ---------------------------------------------------------------------------


class TestBuildSRTString:
    def test_basic(self) -> None:
        srt = build_srt_string(["你好。", "再見。"], [2.0, 3.0])
        assert "1\n" in srt
        assert "2\n" in srt
        assert "你好。" in srt
        assert "再見。" in srt
        assert "00:00:00,000 --> 00:00:02,000" in srt
        assert "00:00:02,000 --> 00:00:05,000" in srt

    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(ValueError):
            build_srt_string(["a", "b"], [1.0])

    def test_empty(self) -> None:
        assert build_srt_string([], []) == ""

    def test_single(self) -> None:
        srt = build_srt_string(["Test."], [5.0])
        assert "1\n" in srt
        assert "00:00:00,000 --> 00:00:05,000" in srt
        assert "Test." in srt


# ---------------------------------------------------------------------------
# write_srt
# ---------------------------------------------------------------------------


class TestWriteSRT:
    def test_writes_file(self, tmp_path) -> None:
        out = tmp_path / "test.srt"
        write_srt(["Hello.", "World."], [1.0, 2.0], out)
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "Hello." in content
        assert "World." in content

    def test_creates_parent_dirs(self, tmp_path) -> None:
        out = tmp_path / "sub" / "dir" / "test.srt"
        write_srt(["Test."], [1.0], out)
        assert out.exists()

    def test_length_mismatch_raises(self, tmp_path) -> None:
        out = tmp_path / "test.srt"
        with pytest.raises(ValueError):
            write_srt(["a"], [1.0, 2.0], out)

    def test_utf8_encoding(self, tmp_path) -> None:
        out = tmp_path / "zh.srt"
        write_srt(["你好世界。"], [2.0], out)
        content = out.read_text(encoding="utf-8")
        assert "你好世界。" in content


# ---------------------------------------------------------------------------
# generate_srt (high-level)
# ---------------------------------------------------------------------------


class TestGenerateSRT:
    def test_uniform_mode(self) -> None:
        text = "你好世界。這是測試！再見。"
        srt = generate_srt(text, total_duration=6.0, mode="uniform")
        assert "1\n" in srt
        assert "2\n" in srt
        assert "3\n" in srt

    def test_rate_mode(self) -> None:
        text = "你好世界。這是測試！再見。"
        srt = generate_srt(text, total_duration=6.0, mode="rate")
        assert srt != ""

    def test_empty_text(self) -> None:
        assert generate_srt("", total_duration=5.0) == ""

    def test_normalizes_input(self) -> None:
        # 雙省略號應被正規化
        srt = generate_srt("等——等……好了。", total_duration=3.0)
        assert srt != ""

    def test_secondary_split(self) -> None:
        long = "一，二，三，四，五，六，七，八，九，十，十一，十二，十三，"
        srt_no_split = generate_srt(long, 5.0, secondary_split=False)
        srt_split = generate_srt(long, 5.0, secondary_split=True, max_length=15)
        # 啟用次要斷句時應有更多句子（SRT 時間箭頭數量更多）
        assert srt_split.count(" --> ") > srt_no_split.count(" --> ")
