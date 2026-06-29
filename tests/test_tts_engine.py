"""Tests for src.tts_engine — TTSEngine, TTSResult."""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest

from src.tts_engine import TTSEngine, TTSResult


class TestTTSResult:
    """TTSResult dataclass 基本測試."""

    def test_create(self) -> None:
        result = TTSResult(
            audio=np.array([0.1, 0.2], dtype=np.float32),
            sample_rate=24000,
            duration=0.5,
            latency_ms=100.0,
            speaker="Vivian",
            language="Chinese",
            text="你好",
        )
        assert result.sample_rate == 24000
        assert result.speaker == "Vivian"
        assert result.duration == 0.5
        assert result.latency_ms == 100.0
        assert result.text == "你好"

    def test_fields_mutable(self) -> None:
        """TTSResult 為一般 dataclass（非 frozen），欄位可修改."""
        result = TTSResult(
            audio=np.array([0.0], dtype=np.float32),
            sample_rate=24000,
            duration=0.0,
            latency_ms=0.0,
            speaker="",
            language="",
            text="",
        )
        result.speaker = "other"  # 應可正常修改
        assert result.speaker == "other"


class TestTTSEngineDemoMode:
    """TTSEngine demo mode（未載入模型時的行為）."""

    @pytest.fixture()
    def engine(self) -> TTSEngine:
        return TTSEngine(model_path="dummy-model", device="cpu")

    def test_is_loaded_initial_false(self, engine: TTSEngine) -> None:
        assert not engine.is_loaded()

    def test_model_type_empty_initial(self, engine: TTSEngine) -> None:
        assert engine.model_type == ""

    def test_synthesize_returns_silence_in_demo(self, engine: TTSEngine) -> None:
        result = engine.synthesize(text="hello", speaker="Vivian", language="Chinese")
        assert isinstance(result, TTSResult)
        assert result.sample_rate == 24000
        assert np.all(result.audio == 0.0)

    def test_voice_design_returns_silence_in_demo(self, engine: TTSEngine) -> None:
        result = engine.voice_design(text="hello", language="Chinese", instruct="warm")
        assert isinstance(result, TTSResult)
        assert result.sample_rate == 24000
        assert np.all(result.audio == 0.0)

    def test_voice_clone_without_ref_raises_in_demo(self, engine: TTSEngine) -> None:
        # demo mode 下 ref_audio 不檢查，但應回傳靜音而非崩潰
        result = engine.voice_clone(text="hello", language="Chinese", ref_audio=None)
        assert isinstance(result, TTSResult)
        assert result.sample_rate == 24000
        assert np.all(result.audio == 0.0)

    def test_unload(self, engine: TTSEngine) -> None:
        engine.unload()
        assert not engine.is_loaded()
        assert engine.model_type == ""


class TestTTSEngineModelTypeCheck:
    """TTSEngine model_type 路由檢查（模擬已載入模型）."""

    @pytest.fixture()
    def engine(self) -> TTSEngine:
        eng = TTSEngine(model_path="dummy", device="cpu")
        # 手動模擬載入狀態
        mock_model = MagicMock()
        mock_model.model.tts_model_type = "custom_voice"
        eng._model = mock_model
        eng._loaded = True
        eng._model_type = "custom_voice"
        return eng

    def test_synthesize_raises_on_wrong_type(self, engine: TTSEngine) -> None:
        engine._model_type = "base"
        with pytest.raises(RuntimeError, match="custom_voice"):
            engine.synthesize(text="test", speaker="Vivian")

    def test_voice_design_raises_on_wrong_type(self, engine: TTSEngine) -> None:
        engine._model_type = "base"
        with pytest.raises(RuntimeError, match="voice_design"):
            engine.voice_design(text="test")

    def test_voice_clone_raises_on_wrong_type(self, engine: TTSEngine) -> None:
        engine._model_type = "custom_voice"
        with pytest.raises(RuntimeError, match="base"):
            engine.voice_clone(text="test", ref_audio=(np.zeros(100), 24000))

    def test_voice_clone_raises_on_no_ref(self, engine: TTSEngine) -> None:
        engine._model_type = "base"
        engine._model.model.tts_model_type = "base"
        with pytest.raises(ValueError, match="ref_audio"):
            engine.voice_clone(text="test", ref_audio=None)

    def test_synthesize_correct_type(self, engine: TTSEngine) -> None:
        """custom_voice 模型應正常執行 synthesize."""
        engine._model.model.tts_model_type = "custom_voice"
        engine._model_type = "custom_voice"
        # mock generate_custom_voice
        fake_wav = [np.array([0.1, 0.2], dtype=np.float32)]
        engine._model.generate_custom_voice.return_value = (fake_wav, 24000)
        result = engine.synthesize(text="test", speaker="Vivian")
        assert result.sample_rate == 24000
        assert result.duration > 0

    def test_voice_design_correct_type(self, engine: TTSEngine) -> None:
        engine._model_type = "voice_design"
        engine._model.model.tts_model_type = "voice_design"
        fake_wav = [np.array([0.1], dtype=np.float32)]
        engine._model.generate_voice_design.return_value = (fake_wav, 24000)
        result = engine.voice_design(text="test", instruct="warm")
        assert result.sample_rate == 24000

    def test_voice_clone_correct_type(self, engine: TTSEngine) -> None:
        engine._model_type = "base"
        engine._model.model.tts_model_type = "base"
        fake_wav = [np.array([0.1], dtype=np.float32)]
        engine._model.generate_voice_clone.return_value = (fake_wav, 24000)
        result = engine.voice_clone(
            text="test",
            ref_audio=(np.zeros(24000, dtype=np.float32), 24000),
        )
        assert result.sample_rate == 24000


class TestTTSEngineUtils:
    """TTSEngine 工具方法測試."""

    def test_to_wav_bytes(self) -> None:
        engine = TTSEngine(model_path="dummy", device="cpu")
        result = TTSResult(
            audio=np.array([0.1, -0.2, 0.0], dtype=np.float32),
            sample_rate=24000,
            duration=0.5,
            latency_ms=10.0,
            speaker="Vivian",
            language="Chinese",
            text="test",
        )
        wav = engine.to_wav_bytes(result)
        assert isinstance(wav, bytes)
        # WAV header 應以 RIFF 開頭
        assert wav[:4] == b"RIFF"

    def test_get_supported_speakers_no_model(self) -> None:
        engine = TTSEngine(model_path="dummy", device="cpu")
        assert engine.get_supported_speakers() == []

    def test_get_supported_languages_no_model(self) -> None:
        engine = TTSEngine(model_path="dummy", device="cpu")
        assert engine.get_supported_languages() == []

    def test_get_supported_speakers_with_model(self) -> None:
        engine = TTSEngine(model_path="dummy", device="cpu")
        mock_model = MagicMock()
        mock_model.model.get_supported_speakers.return_value = {"Vivian", "Serena"}
        engine._model = mock_model
        engine._loaded = True
        speakers = engine.get_supported_speakers()
        assert "Vivian" in speakers

    def test_get_supported_languages_with_model(self) -> None:
        engine = TTSEngine(model_path="dummy", device="cpu")
        mock_model = MagicMock()
        mock_model.model.get_supported_languages.return_value = ["chinese", "english"]
        engine._model = mock_model
        engine._loaded = True
        langs = engine.get_supported_languages()
        assert "Chinese" in langs
        assert "English" in langs
