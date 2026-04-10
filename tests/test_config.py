"""Tests for src.config module."""

from __future__ import annotations

from pathlib import Path

from src.config import BUILTIN_SPEAKERS, SUPPORTED_TTS_LANGUAGES, AppSettings, TTSSettings


class TestTTSSettings:
    def test_defaults(self) -> None:
        s = TTSSettings()
        assert s.model_path == "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
        assert s.srt_mode == "uniform"
        assert s.zh_cpm == 160
        assert s.en_wpm == 150
        assert s.device == "cuda:0"
        assert s.port == 8990

    def test_custom_values(self) -> None:
        s = TTSSettings(device="cpu", port=9999)
        assert s.device == "cpu"
        assert s.port == 9999


class TestAppSettings:
    def test_default_locale(self) -> None:
        s = AppSettings()
        assert s.locale == "zh-TW"

    def test_save_and_load(self, tmp_path: Path, monkeypatch: object) -> None:
        config_file = tmp_path / "config.json"
        import src.config as config_mod

        monkeypatch.setattr(config_mod, "_CONFIG_FILE", config_file)  # type: ignore[attr-defined]

        settings = AppSettings(locale="en")
        settings.save()
        assert config_file.exists()

        loaded = AppSettings.load()
        assert loaded.locale == "en"


class TestConstants:
    def test_builtin_speakers(self) -> None:
        assert len(BUILTIN_SPEAKERS) == 9
        assert "Vivian" in BUILTIN_SPEAKERS

    def test_supported_languages(self) -> None:
        assert "Chinese" in SUPPORTED_TTS_LANGUAGES
        assert "English" in SUPPORTED_TTS_LANGUAGES
        assert len(SUPPORTED_TTS_LANGUAGES) == 10
