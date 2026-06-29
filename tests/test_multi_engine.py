"""Tests for src.multi_engine — ModelPool."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.multi_engine import ModelPool


class TestModelPoolInitial:
    """ModelPool 初始狀態測試."""

    @pytest.fixture()
    def pool(self) -> ModelPool:
        return ModelPool(
            custom_voice_path="mock-cv",
            voice_design_path="mock-vd",
            base_path="mock-base",
            device="cpu",
        )

    def test_initial_loaded_kinds_empty(self, pool: ModelPool) -> None:
        assert pool.loaded_kinds() == []

    def test_initial_is_loaded_false(self, pool: ModelPool) -> None:
        assert not pool.is_loaded("base")
        assert not pool.is_loaded("custom_voice")
        assert not pool.is_loaded("voice_design")

    def test_get_invalid_kind_raises(self, pool: ModelPool) -> None:
        with pytest.raises(ValueError, match="不支援"):
            pool.get("invalid_kind")


class TestModelPoolGet:
    """ModelPool.get() 行為測試."""

    @pytest.fixture()
    def pool(self) -> ModelPool:
        return ModelPool(
            custom_voice_path="mock-cv",
            voice_design_path="mock-vd",
            base_path="mock-base",
            device="cpu",
        )

    def test_get_creates_engine_on_first_call(self, pool: ModelPool) -> None:
        with (
            patch.object(pool, "_ensure_downloaded"),
            patch("src.multi_engine.TTSEngine") as mock_engine_cls,
        ):
            mock_engine = MagicMock()
            mock_engine.is_loaded.return_value = True
            mock_engine_cls.return_value = mock_engine

            engine = pool.get("base")

            mock_engine_cls.assert_called_once_with(
                model_path="mock-base", device="cpu"
            )
            mock_engine.load_model.assert_called_once()
            assert engine is mock_engine

    def test_get_returns_cached_on_second_call(self, pool: ModelPool) -> None:
        with (
            patch.object(pool, "_ensure_downloaded"),
            patch("src.multi_engine.TTSEngine") as mock_engine_cls,
        ):
            mock_engine = MagicMock()
            mock_engine.is_loaded.return_value = True
            mock_engine_cls.return_value = mock_engine

            first = pool.get("base")
            second = pool.get("base")

            assert first is second
            # TTSEngine 建構函式應只被呼叫一次
            mock_engine_cls.assert_called_once()

    def test_get_different_kinds_create_separate_engines(self, pool: ModelPool) -> None:
        with (
            patch.object(pool, "_ensure_downloaded"),
            patch("src.multi_engine.TTSEngine") as mock_engine_cls,
        ):
            mock_engine_cls.side_effect = [
                MagicMock(is_loaded=lambda: True),
                MagicMock(is_loaded=lambda: True),
            ]

            cv = pool.get("custom_voice")
            vd = pool.get("voice_design")

            assert cv is not vd
            assert mock_engine_cls.call_count == 2

    def test_loaded_kinds_after_get(self, pool: ModelPool) -> None:
        with (
            patch.object(pool, "_ensure_downloaded"),
            patch("src.multi_engine.TTSEngine") as mock_engine_cls,
        ):
            mock_engine = MagicMock()
            mock_engine.is_loaded.return_value = True
            mock_engine_cls.return_value = mock_engine

            pool.get("base")
            pool.get("custom_voice")

            kinds = pool.loaded_kinds()
            assert "base" in kinds
            assert "custom_voice" in kinds


class TestModelPoolEnsureDownloaded:
    """ModelPool._ensure_downloaded() 測試."""

    @pytest.fixture()
    def pool(self) -> ModelPool:
        return ModelPool(
            custom_voice_path="Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
            voice_design_path="Qwen/Qwen3-TTS-12Hz-0.6B-VoiceDesign",
            base_path="Qwen/Qwen3-TTS-12Hz-0.6B-Base",
            device="cpu",
        )

    def test_ensure_downloaded_success(self, pool: ModelPool) -> None:
        with patch("src.multi_engine.Path.exists", return_value=False), patch(
            "src.model_manager.ensure_tts_model_available",
            return_value="local-path",
        ) as mock_fn:
            # 不應拋出
            pool._ensure_downloaded("Qwen/Qwen3-TTS-12Hz-0.6B-Base")
            mock_fn.assert_called_once()

    def test_ensure_downloaded_local_path_skips_download(self, pool: ModelPool) -> None:
        with patch("src.multi_engine.Path.exists", return_value=True), patch(
            "src.model_manager.ensure_tts_model_available",
        ) as mock_fn:
            pool._ensure_downloaded("C:/local/model")
            mock_fn.assert_not_called()


class TestModelPoolUnload:
    """ModelPool unload/unload_all 測試."""

    @pytest.fixture()
    def pool_with_engines(self) -> ModelPool:
        pool = ModelPool(
            custom_voice_path="mock-cv",
            voice_design_path="mock-vd",
            base_path="mock-base",
            device="cpu",
        )
        # 手動注入 mock engines
        base_mock = MagicMock()
        base_mock.is_loaded.return_value = True
        cv_mock = MagicMock()
        cv_mock.is_loaded.return_value = True
        pool._engines = {"base": base_mock, "custom_voice": cv_mock}
        return pool

    def test_unload_removes_engine(self, pool_with_engines: ModelPool) -> None:
        pool_with_engines.unload("base")
        assert "base" not in pool_with_engines._engines
        assert "custom_voice" in pool_with_engines._engines

    def test_unload_calls_engine_unload(self, pool_with_engines: ModelPool) -> None:
        engine = pool_with_engines._engines["base"]
        pool_with_engines.unload("base")
        engine.unload.assert_called_once()

    def test_unload_non_existent_does_nothing(self, pool_with_engines: ModelPool) -> None:
        pool_with_engines.unload("voice_design")  # 不應拋出

    def test_unload_all_removes_all(self, pool_with_engines: ModelPool) -> None:
        pool_with_engines.unload_all()
        assert pool_with_engines._engines == {}
