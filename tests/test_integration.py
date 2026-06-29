"""Integration tests for qwen3-voice-studio.

這些測試驗證模組間的協作是否正常，不啟動實際 Gradio UI。
"""

from __future__ import annotations

import numpy as np

from src.audio_utils import to_gradio_audio
from src.tts_engine import TTSResult


class TestAudioToGradioIntegration:
    """to_gradio_audio + TTSResult 的整合測試."""

    def test_ttsresult_to_gradio_audio(self) -> None:
        """TTSResult 的 audio 可以安全傳遞給 to_gradio_audio."""
        result = TTSResult(
            audio=np.array([0.5, -0.3, 0.0], dtype=np.float32),
            sample_rate=24000,
            duration=0.5,
            latency_ms=100.0,
            speaker="Vivian",
            language="Chinese",
            text="test",
        )
        sr, audio_int16 = to_gradio_audio(result.audio, result.sample_rate)
        assert sr == 24000
        assert audio_int16.dtype == np.int16
        assert len(audio_int16) == 3


class TestSRTFullChain:
    """SRT 生成完整鏈路測試：normalize → split → allocate → format."""

    def test_uniform_mode_full_chain(self) -> None:
        from utils.srt_generator import generate_srt

        text = "你好世界。這是測試！"
        srt = generate_srt(text, total_duration=6.0, mode="uniform")
        assert "1" in srt
        assert "2" in srt
        assert "你好世界。" in srt
        assert "這是測試！" in srt
        assert "-->" in srt

    def test_rate_mode_full_chain(self) -> None:
        from utils.srt_generator import generate_srt

        text = "你好世界。Hello world!"
        srt = generate_srt(text, total_duration=6.0, mode="rate")
        assert srt != ""
        assert srt.count("-->") == 2

    def test_empty_text_returns_empty(self) -> None:
        from utils.srt_generator import generate_srt

        assert generate_srt("", total_duration=5.0) == ""


class TestFormatSRTDelegation:
    """驗證 src.audio_utils.format_srt_time 委派至 utils.srt_generator."""

    def test_delegation_produces_same_result(self) -> None:
        from src.audio_utils import format_srt_time as fmt_old
        from utils.srt_generator import format_srt_timestamp as fmt_new

        test_cases = [0.0, 1.0, 60.0, 3600.0, 3661.5, 0.123, 59.999, 1.2345]
        for t in test_cases:
            assert fmt_old(t) == fmt_new(t), f"Mismatch for {t}"

    def test_negative_handled_same(self) -> None:
        from src.audio_utils import format_srt_time as fmt_old
        from utils.srt_generator import format_srt_timestamp as fmt_new

        assert fmt_old(-1.0) == fmt_new(-1.0) == "00:00:00,000"
