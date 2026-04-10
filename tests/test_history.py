"""Tests for src.history module."""

from __future__ import annotations

from pathlib import Path

from src.history import HistoryManager


class TestHistoryManager:
    def test_add_and_search(self, tmp_path: Path) -> None:
        mgr = HistoryManager(base_dir=tmp_path)
        mgr.add_record(
            text_preview="你好世界",
            full_text="你好世界",
            speaker="Vivian",
            language="Chinese",
            duration=1.5,
        )
        results = mgr.search("你好")
        assert len(results) == 1

    def test_to_table_data(self, tmp_path: Path) -> None:
        mgr = HistoryManager(base_dir=tmp_path)
        mgr.add_record(
            text_preview="Test",
            full_text="Test full",
            speaker="Eric",
            language="English",
            duration=2.0,
        )
        data = mgr.to_table_data()
        assert len(data) == 1
        assert "Eric" in data[0]

    def test_max_records(self, tmp_path: Path) -> None:
        mgr = HistoryManager(base_dir=tmp_path, max_records=3)
        for i in range(5):
            mgr.add_record(
                text_preview=f"Record {i}",
                full_text=f"Record {i}",
                speaker="Vivian",
                language="Chinese",
                duration=1.0,
            )
        assert len(mgr.to_table_data()) == 3

    def test_clear(self, tmp_path: Path) -> None:
        mgr = HistoryManager(base_dir=tmp_path)
        mgr.add_record(
            text_preview="to clear",
            full_text="to clear",
            speaker="Vivian",
            language="Chinese",
            duration=1.0,
        )
        mgr.clear()
        assert len(mgr.to_table_data()) == 0
