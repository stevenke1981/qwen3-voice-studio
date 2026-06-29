"""Tests for src.voice_library — VoiceLibrary, VoiceProfile."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.voice_library import VoiceLibrary, VoiceProfile


class TestVoiceProfile:
    """VoiceProfile dataclass 測試."""

    def test_defaults(self) -> None:
        p = VoiceProfile(name="test", speaker="Vivian", language="Chinese")
        assert p.name == "test"
        assert p.speaker == "Vivian"
        assert p.instruct == ""
        assert p.pitch == 1.0
        assert p.speed == 1.0
        assert p.energy == 1.0
        assert p.volume == 1.0
        assert p.emotion == "neutral"

    def test_custom_values(self) -> None:
        p = VoiceProfile(
            name="custom",
            speaker="Eric",
            language="English",
            instruct="warm",
            pitch=1.2,
            speed=0.8,
            energy=1.5,
            volume=0.9,
            emotion="happy",
        )
        assert p.instruct == "warm"
        assert p.pitch == 1.2

    def test_frozen(self) -> None:
        p = VoiceProfile(name="frozen", speaker="Vivian", language="Chinese")
        with pytest.raises(AttributeError):
            p.name = "changed"  # type: ignore[misc]


class TestVoiceLibrary:
    """VoiceLibrary 操作測試."""

    @pytest.fixture()
    def lib(self, tmp_path: Path) -> VoiceLibrary:
        return VoiceLibrary(base_dir=tmp_path)

    def test_save_and_list(self, lib: VoiceLibrary) -> None:
        profile = VoiceProfile(name="test_voice", speaker="Vivian", language="Chinese")
        lib.save(profile)
        profiles = lib.list_all()
        assert len(profiles) == 1
        assert profiles[0].name == "test_voice"

    def test_list_voices(self, lib: VoiceLibrary) -> None:
        lib.save(VoiceProfile(name="b", speaker="Vivian", language="Chinese"))
        lib.save(VoiceProfile(name="a", speaker="Eric", language="English"))
        names = lib.list_voices()
        assert names == ["a", "b"]  # 排序

    def test_delete_existing(self, lib: VoiceLibrary) -> None:
        lib.save(VoiceProfile(name="to_delete", speaker="Eric", language="English"))
        assert lib.delete("to_delete")
        assert len(lib.list_all()) == 0

    def test_delete_nonexistent(self, lib: VoiceLibrary) -> None:
        assert not lib.delete("nonexistent")

    def test_get_voice_existing(self, lib: VoiceLibrary) -> None:
        lib.save(VoiceProfile(name="my_voice", speaker="Vivian", language="Chinese"))
        profile = lib.get_voice("my_voice")
        assert profile is not None
        assert profile.speaker == "Vivian"

    def test_get_voice_nonexistent(self, lib: VoiceLibrary) -> None:
        assert lib.get_voice("ghost") is None

    def test_path_traversal_blocked(self, lib: VoiceLibrary) -> None:
        with pytest.raises(ValueError, match="[Ii]nvalid"):
            lib.save(VoiceProfile(name="../evil", speaker="Vivian", language="Chinese"))

    def test_path_traversal_windows_blocked(self, lib: VoiceLibrary) -> None:
        with pytest.raises(ValueError, match="[Ii]nvalid"):
            lib.save(VoiceProfile(name="..\\evil", speaker="Vivian", language="Chinese"))

    def test_save_persistence(self, tmp_path: Path) -> None:
        """儲存後新實例應能讀取."""
        lib1 = VoiceLibrary(base_dir=tmp_path)
        lib1.save(VoiceProfile(name="persist", speaker="Vivian", language="Chinese"))

        lib2 = VoiceLibrary(base_dir=tmp_path)
        assert len(lib2.list_all()) == 1
        assert lib2.get_voice("persist") is not None

    def test_save_sanitizes_name(self, lib: VoiceLibrary) -> None:
        """特殊字元應被 sanitize."""
        lib.save(VoiceProfile(name="hello world!", speaker="Vivian", language="Chinese"))
        assert lib.get_voice("hello world!") is not None
