"""Tests for src.i18n module."""

from __future__ import annotations

from src.i18n import add_translation, get_all_keys, get_translations_for_locale, t


class TestTranslationFunction:
    """t() 函式測試."""

    def test_returns_zh_tw_by_default(self) -> None:
        result = t("tab_tts")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_english(self) -> None:
        result = t("tab_tts", "en")
        assert result == "📝 Text to Speech"

    def test_missing_key_returns_key(self) -> None:
        result = t("nonexistent_key_xyz", "zh-TW")
        assert result == "nonexistent_key_xyz"

    def test_missing_locale_falls_back_to_default(self) -> None:
        result = t("tab_tts", "fr")
        # Falls back to DEFAULT_LOCALE (zh-TW) when locale not found
        assert result == t("tab_tts", "zh-TW")

    def test_all_keys_have_both_locales(self) -> None:
        keys = get_all_keys()
        for key in keys:
            zh = t(key, "zh-TW")
            en = t(key, "en")
            assert zh != key, f"zh-TW missing for {key}"
            assert en != key, f"en missing for {key}"


class TestGetAllKeys:
    def test_returns_non_empty_set(self) -> None:
        keys = get_all_keys()
        assert len(keys) > 10

    def test_contains_expected_keys(self) -> None:
        keys = get_all_keys()
        assert "tab_tts" in keys
        assert "tab_batch" in keys
        assert "tab_voice" in keys


class TestGetTranslationsForLocale:
    def test_zh_tw_dict(self) -> None:
        d = get_translations_for_locale("zh-TW")
        assert isinstance(d, dict)
        assert "tab_tts" in d

    def test_en_dict(self) -> None:
        d = get_translations_for_locale("en")
        assert isinstance(d, dict)
        assert d["tab_tts"] == "📝 Text to Speech"


class TestAddTranslation:
    def test_add_new_key(self) -> None:
        add_translation("_test_key_001", {"zh-TW": "測試", "en": "Test"})
        assert t("_test_key_001", "zh-TW") == "測試"
        assert t("_test_key_001", "en") == "Test"
