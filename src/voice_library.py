"""Qwen3 Voice Studio — 聲音圖書館."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_VOICE_DIR = Path.home() / ".qwen3-voice-studio" / "voices"


@dataclass(frozen=True)
class VoiceProfile:
    """聲音設定檔."""

    name: str
    speaker: str
    language: str
    instruct: str = ""
    pitch: float = 1.0
    speed: float = 1.0
    energy: float = 1.0
    volume: float = 1.0
    emotion: str = "neutral"


@dataclass
class VoiceLibrary:
    """聲音圖書館管理器."""

    base_dir: Path | None = None
    _voices: dict[str, VoiceProfile] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.base_dir is None:
            self.base_dir = _DEFAULT_VOICE_DIR
        else:
            self.base_dir = Path(self.base_dir)
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        """從磁碟載入已儲存的聲音."""
        if not self.base_dir.exists():
            return
        for f in self.base_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                profile = VoiceProfile(**data)
                self._voices[profile.name] = profile
            except Exception as e:
                logger.warning("Failed to load voice %s: %s", f.name, e)

    def save_voice(self, profile: VoiceProfile) -> None:
        """儲存聲音設定."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        # 防止路徑穿越
        if ".." in profile.name or "/" in profile.name or "\\" in profile.name:
            raise ValueError("Invalid voice name: path traversal detected")
        safe_name = "".join(c for c in profile.name if c.isalnum() or c in "- _")
        if not safe_name:
            raise ValueError("Invalid voice name")
        file_path = self.base_dir / f"{safe_name}.json"
        data = {
            "name": profile.name,
            "speaker": profile.speaker,
            "language": profile.language,
            "instruct": profile.instruct,
            "pitch": profile.pitch,
            "speed": profile.speed,
            "energy": profile.energy,
            "volume": profile.volume,
            "emotion": profile.emotion,
        }
        file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self._voices = {**self._voices, profile.name: profile}

    def delete_voice(self, name: str) -> bool:
        """刪除聲音設定."""
        if name not in self._voices:
            return False
        safe_name = "".join(c for c in name if c.isalnum() or c in "-_ ")
        file_path = self.base_dir / f"{safe_name}.json"
        if file_path.exists():
            file_path.unlink()
        self._voices = {k: v for k, v in self._voices.items() if k != name}
        return True

    def get_voice(self, name: str) -> VoiceProfile | None:
        return self._voices.get(name)

    def list_voices(self) -> list[str]:
        return sorted(self._voices.keys())

    def get_all_profiles(self) -> list[VoiceProfile]:
        return [self._voices[k] for k in sorted(self._voices)]

    # ── Aliases for convenience ──
    save = save_voice
    delete = delete_voice
    list_all = get_all_profiles
