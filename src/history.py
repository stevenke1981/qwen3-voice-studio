"""Qwen3 Voice Studio — 歷史記錄管理."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_HISTORY_DIR = Path.home() / ".qwen3-voice-studio" / "history"


@dataclass(frozen=True)
class HistoryRecord:
    """歷史記錄項目."""

    id: str
    timestamp: str
    text_preview: str
    full_text: str
    speaker: str
    language: str
    duration: float
    audio_path: str
    srt_path: str = ""


@dataclass
class HistoryManager:
    """歷史記錄管理器."""

    base_dir: Path | None = None
    _records: list[HistoryRecord] = field(default_factory=list)
    max_records: int = 200

    def __post_init__(self) -> None:
        if self.base_dir is None:
            self.base_dir = _DEFAULT_HISTORY_DIR
        else:
            self.base_dir = Path(self.base_dir)
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        """載入歷史記錄."""
        index_file = self.base_dir / "index.json"
        if not index_file.exists():
            return
        try:
            data = json.loads(index_file.read_text(encoding="utf-8"))
            self._records = [HistoryRecord(**r) for r in data]
        except Exception as e:
            logger.warning("Failed to load history: %s", e)

    def _save_index(self) -> None:
        """儲存索引."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        index_file = self.base_dir / "index.json"
        data = []
        for r in self._records:
            data.append({
                "id": r.id,
                "timestamp": r.timestamp,
                "text_preview": r.text_preview,
                "full_text": r.full_text,
                "speaker": r.speaker,
                "language": r.language,
                "duration": r.duration,
                "audio_path": r.audio_path,
                "srt_path": r.srt_path,
            })
        index_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add_record(
        self,
        text: str = "",
        speaker: str = "",
        language: str = "",
        duration: float = 0.0,
        audio_path: str = "",
        srt_path: str = "",
        *,
        text_preview: str = "",
        full_text: str = "",
    ) -> HistoryRecord:
        """新增歷史記錄."""
        now = datetime.now(tz=timezone.utc)
        record_id = now.strftime("%Y%m%d_%H%M%S_%f")
        resolved_text = full_text or text
        preview = text_preview or (resolved_text[:80] + "..." if len(resolved_text) > 80 else resolved_text)

        record = HistoryRecord(
            id=record_id,
            timestamp=now.isoformat(timespec="seconds"),
            text_preview=preview,
            full_text=resolved_text,
            speaker=speaker,
            language=language,
            duration=duration,
            audio_path=audio_path,
            srt_path=srt_path,
        )

        new_records = [record, *self._records]
        if len(new_records) > self.max_records:
            new_records = new_records[: self.max_records]
        self._records = new_records
        self._save_index()
        return record

    def search(self, query: str) -> list[HistoryRecord]:
        """搜尋歷史記錄."""
        if not query:
            return list(self._records)
        q = query.lower()
        return [
            r
            for r in self._records
            if q in r.full_text.lower() or q in r.speaker.lower()
        ]

    def get_all(self) -> list[HistoryRecord]:
        return list(self._records)

    def to_table_data(self) -> list[list[str]]:
        """轉換為表格資料 (Gradio Dataframe 格式)."""
        return [
            [r.timestamp, r.text_preview, r.speaker, r.language, f"{r.duration:.1f}s"]
            for r in self._records
        ]

    def clear(self) -> None:
        """清除所有歷史記錄."""
        self._records = []
        self._save_index()
