"""Pytest conftest — 共用 fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    """提供乾淨的暫存目錄."""
    return tmp_path


@pytest.fixture()
def sample_text() -> str:
    return "你好世界。這是一段測試文字。Hello world!"


@pytest.fixture()
def sample_text_file(tmp_path: Path) -> Path:
    """建立測試用文字檔."""
    p = tmp_path / "test.txt"
    p.write_text("第一句話。\n第二句話。\n第三句話。", encoding="utf-8")
    return p
