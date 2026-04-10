"""Qwen3 Voice Studio — 音訊工具."""

from __future__ import annotations

import io
import re
from pathlib import Path

import numpy as np


def to_gradio_audio(audio: np.ndarray, sample_rate: int) -> tuple[int, np.ndarray]:
    """將 float32 音訊安全轉換為 Gradio 接受的 (sample_rate, int16) 格式.

    Gradio 的 processing_utils 在轉換 float32 → int16 時，若音訊全為零會
    觸發 division-by-zero（RuntimeWarning）並產生 NaN，進而導致 invalid cast。
    此函式在傳入 Gradio 前自行做安全正規化，避免上述問題。
    """
    audio = np.asarray(audio, dtype=np.float32)
    max_val = float(np.abs(audio).max())
    if max_val > 0:
        audio = audio / max_val
    # clip 防止極罕見浮點溢位再轉 int16
    audio_int16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
    return sample_rate, audio_int16


def read_text_file(file_path: str | Path) -> str:
    """讀取文字檔案 (.txt / .md).

    Args:
        file_path: 檔案路徑

    Returns:
        檔案內容

    Raises:
        ValueError: 不支援的格式或檔案過大
    """
    path = Path(file_path)

    if path.suffix.lower() not in (".txt", ".md"):
        raise ValueError(f"Unsupported file format: {path.suffix}")

    max_size = 10 * 1024 * 1024  # 10 MB
    if path.stat().st_size > max_size:
        raise ValueError("File too large (max 10 MB)")

    return path.read_text(encoding="utf-8")


def split_text_to_sentences(text: str) -> list[str]:
    """將文字切分為句子.

    支援中英文句號、問號、驚嘆號作為斷句依據。
    """
    sentences = re.split(r"(?<=[。！？.!?\n])\s*", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def format_srt_time(seconds: float) -> str:
    """將秒數轉為 SRT 時間格式 HH:MM:SS,mmm.

    Args:
        seconds: 秒數（浮點）

    Returns:
        格式化時間字串
    """
    if seconds < 0:
        seconds = 0.0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def save_wav_bytes(audio_data: bytes, output_path: str | Path) -> Path:
    """儲存 WAV 位元組到檔案."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(audio_data)
    return path


def wav_bytes_to_buffer(audio_data: bytes) -> io.BytesIO:
    """將 WAV bytes 轉為 BytesIO buffer."""
    buf = io.BytesIO(audio_data)
    buf.seek(0)
    return buf
