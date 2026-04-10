"""Qwen3 Voice Studio — 錯誤處理系統."""

from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ErrorRecord:
    """不可變的錯誤記錄."""

    timestamp: str
    level: str
    message: str
    detail: str = ""


@dataclass
class ErrorHandler:
    """錯誤日誌管理器."""

    _records: list[ErrorRecord] = field(default_factory=list)
    max_records: int = 500

    def add_error(
        self,
        message: str,
        detail: str = "",
        level: str = "ERROR",
    ) -> ErrorRecord:
        """新增錯誤記錄."""
        record = ErrorRecord(
            timestamp=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
            level=level,
            message=message,
            detail=detail,
        )
        # 不可變 list 操作：建立新 list
        new_records = [*self._records, record]
        if len(new_records) > self.max_records:
            new_records = new_records[-self.max_records :]
        self._records = new_records
        logger.log(
            logging.getLevelName(level) if isinstance(level, str) else level,
            "%s: %s",
            message,
            detail,
        )
        return record

    def get_errors(self) -> list[ErrorRecord]:
        """取得所有錯誤記錄（副本）."""
        return list(self._records)

    def clear(self) -> None:
        """清除所有錯誤記錄."""
        self._records = []

    def format_for_display(self) -> str:
        """格式化錯誤記錄為顯示文字."""
        if not self._records:
            return ""
        lines = []
        for r in self._records:
            line = f"[{r.timestamp}] [{r.level}] {r.message}"
            if r.detail:
                line += f"\n  → {r.detail}"
            lines.append(line)
        return "\n\n".join(lines)

    def export_csv(self) -> str:
        """匯出錯誤記錄為 CSV 字串."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp", "level", "message", "detail"])
        for r in self._records:
            writer.writerow([r.timestamp, r.level, r.message, r.detail])
        return output.getvalue()

    @property
    def count(self) -> int:
        return len(self._records)
