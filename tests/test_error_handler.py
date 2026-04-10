"""Tests for src.error_handler module."""

from __future__ import annotations

from pathlib import Path

from src.error_handler import ErrorHandler


class TestErrorHandler:
    def test_add_and_display(self) -> None:
        handler = ErrorHandler()
        handler.add_error("TTS", "Something went wrong")
        display = handler.format_for_display()
        assert "TTS" in display
        assert "Something went wrong" in display

    def test_max_records(self) -> None:
        handler = ErrorHandler(max_records=5)
        for i in range(10):
            handler.add_error("Test", f"Error {i}")
        display = handler.format_for_display()
        assert "Error 9" in display
        assert "Error 0" not in display

    def test_clear(self) -> None:
        handler = ErrorHandler()
        handler.add_error("TTS", "error")
        handler.clear()
        assert handler.format_for_display() == ""

    def test_export_csv(self) -> None:
        handler = ErrorHandler()
        handler.add_error("TTS", "test error")
        csv_str = handler.export_csv()
        assert isinstance(csv_str, str)
        assert "TTS" in csv_str
        assert "test error" in csv_str


class TestVoiceLibrary:
    """src.voice_library 的基本測試."""

    def test_save_and_list(self, tmp_path: Path) -> None:
        from src.voice_library import VoiceLibrary, VoiceProfile

        lib = VoiceLibrary(base_dir=tmp_path)
        profile = VoiceProfile(name="test_voice", speaker="Vivian", language="Chinese")
        lib.save(profile)
        profiles = lib.list_all()
        assert len(profiles) == 1
        assert profiles[0].name == "test_voice"

    def test_delete(self, tmp_path: Path) -> None:
        from src.voice_library import VoiceLibrary, VoiceProfile

        lib = VoiceLibrary(base_dir=tmp_path)
        profile = VoiceProfile(name="to_delete", speaker="Eric", language="English")
        lib.save(profile)
        lib.delete("to_delete")
        assert len(lib.list_all()) == 0

    def test_path_traversal_blocked(self, tmp_path: Path) -> None:
        from src.voice_library import VoiceLibrary, VoiceProfile

        lib = VoiceLibrary(base_dir=tmp_path)
        import pytest

        with pytest.raises(ValueError, match="[Ii]nvalid"):
            lib.save(VoiceProfile(name="../evil", speaker="Vivian", language="Chinese"))
