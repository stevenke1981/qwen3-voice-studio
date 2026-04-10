"""Qwen3 Voice Studio — 句子級 SRT 生成器.

本模組採用「純句子級時間分配」策略，無需 ForcedAligner 或 ASR。

兩種時間分配模式：
  Mode A (uniform) — 均等分配：total_duration / sentence_count
  Mode B (rate)    — 速率估算：依中文字數 / 英文字數推算各句比例，缺口由最後一句補足

支援中英文混合文本。
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 標點符號集合
# ---------------------------------------------------------------------------

# 主要斷句符號（中文 + 英文）
_PRIMARY_PUNCT_ZH = r"[。！？…；]"
_PRIMARY_PUNCT_EN = r"[.!?]"
_PRIMARY_SPLIT = re.compile(r"(?<=[。！？…；.!?])")

# 次要斷句符號（長句分段）
_SECONDARY_SPLIT = re.compile(r"(?<=[，、；,;\n])")

# 空白行或換行
_NEWLINE_SPLIT = re.compile(r"\n{2,}")

# 偵測中文字元（用於速率計算）
_ZH_PATTERN = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")

# 偵測英文單字（用於速率計算）
_EN_WORD_PATTERN = re.compile(r"[a-zA-Z]+(?:['-][a-zA-Z]+)*")


# ---------------------------------------------------------------------------
# 文字前處理
# ---------------------------------------------------------------------------


def normalize_text(text: str) -> str:
    """正規化文字。

    - 去除首尾空白
    - 合併連續空白為單一空白
    - 統一全形符號（…… → …）
    - 移除零寬字元

    Args:
        text: 原始輸入文字

    Returns:
        正規化後的文字
    """
    if not text:
        return ""

    # 移除零寬字元
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)

    # 全形省略號統一
    text = text.replace("……", "…").replace("...", "…")

    # 合併連續空白（保留換行）
    text = re.sub(r"[ \t]+", " ", text)

    # 去除每行首尾空白
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines)

    # 去除首尾空白
    text = text.strip()

    return text


# ---------------------------------------------------------------------------
# 斷句
# ---------------------------------------------------------------------------


def split_sentences(
    text: str,
    secondary_split: bool = False,
    max_length: int = 100,
) -> list[str]:
    """將文字切分為句子列表。

    優先以主要句末標點（。！？…；.!?）分句；
    secondary_split=True 時，超過 max_length 的句子再以次要標點（，、；,;）細分。

    Args:
        text: 正規化後的文字
        secondary_split: 是否啟用次要斷句
        max_length: 觸發次要斷句的字元長度閾值

    Returns:
        非空句子列表（已 strip）
    """
    if not text:
        return []

    # 先依空白行分段
    paragraphs = _NEWLINE_SPLIT.split(text)

    sentences: list[str] = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # 主要斷句：在標點後分割，保留標點於前句
        parts = _primary_split(para)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if secondary_split and len(part) > max_length:
                sub = _secondary_split(part)
                sentences.extend(s for s in sub if s.strip())
            else:
                sentences.append(part)

    return sentences


def _primary_split(text: str) -> list[str]:
    """以主要標點分句，標點保留在句尾。"""
    # 在標點符號後切割（lookahead 保留標點在前句）
    parts = re.split(r"(?<=[。！？…；.!?])\s*", text)
    return [p for p in parts if p.strip()]


def _secondary_split(text: str) -> list[str]:
    """以次要標點（逗號等）分句，標點保留在句尾。"""
    parts = re.split(r"(?<=[，、；,;\n])\s*", text)
    return [p for p in parts if p.strip()]


# ---------------------------------------------------------------------------
# 時間分配
# ---------------------------------------------------------------------------


def allocate_uniform_durations(
    sentences: list[str],
    total_duration: float,
) -> list[float]:
    """均等分配模式（Mode A）。

    每句時長 = total_duration / len(sentences)。
    最後一句補足浮點誤差。

    Args:
        sentences: 句子列表
        total_duration: 音訊總時長（秒）

    Returns:
        各句時長列表，順序對應 sentences，總和等於 total_duration
    """
    n = len(sentences)
    if n == 0:
        return []
    if total_duration <= 0.0:
        return [0.0] * n

    per = total_duration / n
    durations = [per] * n
    # 修正浮點誤差
    durations[-1] = total_duration - per * (n - 1)
    return durations


def allocate_rate_based_durations(
    sentences: list[str],
    total_duration: float,
    zh_cpm: int = 160,
    en_wpm: int = 150,
) -> list[float]:
    """速率估算模式（Mode B）。

    依每句的中文字數（÷zh_cpm）及英文字數（÷en_wpm）估算閱讀時間，
    再正規化為 total_duration 的比例。
    如句子沒有可識別字元，則以字元數估算（÷ 平均 5 chars/s）。

    Args:
        sentences: 句子列表
        total_duration: 音訊總時長（秒）
        zh_cpm: 中文朗讀速率（字/分鐘，預設 160）
        en_wpm: 英文朗讀速率（字/分鐘，預設 150）

    Returns:
        各句時長列表，總和等於 total_duration
    """
    n = len(sentences)
    if n == 0:
        return []
    if total_duration <= 0.0:
        return [0.0] * n

    weights: list[float] = []
    for sent in sentences:
        zh_chars = len(_ZH_PATTERN.findall(sent))
        en_words = len(_EN_WORD_PATTERN.findall(sent))
        other_chars = len(sent) - zh_chars  # 包含英文、標點、空白

        # 估算閱讀秒數（分鐘速率 → 秒速率）
        zh_seconds = zh_chars / (zh_cpm / 60.0) if zh_chars > 0 else 0.0
        en_seconds = en_words / (en_wpm / 60.0) if en_words > 0 else 0.0

        if zh_seconds == 0.0 and en_seconds == 0.0:
            # fallback：其他字元以 5 chars/s 估算
            weight = max(other_chars / 5.0, 0.1)
        else:
            weight = zh_seconds + en_seconds

        weights.append(weight)

    total_weight = sum(weights)
    if total_weight == 0.0:
        return allocate_uniform_durations(sentences, total_duration)

    durations = [w / total_weight * total_duration for w in weights]
    # 修正浮點誤差
    assigned = sum(durations[:-1])
    durations[-1] = total_duration - assigned
    return durations


# ---------------------------------------------------------------------------
# SRT 格式化
# ---------------------------------------------------------------------------


def format_srt_timestamp(seconds: float) -> str:
    """將秒數轉換為 SRT 時間戳格式 HH:MM:SS,mmm。

    Args:
        seconds: 秒數（非負浮點數）

    Returns:
        格式字串，例如 "00:01:23,456"
    """
    seconds = max(0.0, seconds)
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1_000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# ---------------------------------------------------------------------------
# SRT 寫入
# ---------------------------------------------------------------------------


def write_srt(
    sentences: list[str],
    durations: list[float],
    output_path: str | Path,
    *,
    encoding: str = "utf-8",
) -> None:
    """將句子與對應時長寫入 SRT 檔案。

    Args:
        sentences: 句子列表
        durations: 各句時長（秒），長度需與 sentences 相同
        output_path: 輸出 .srt 檔案路徑
        encoding: 檔案編碼（預設 utf-8）

    Raises:
        ValueError: sentences 與 durations 長度不符
        OSError: 無法寫入目標路徑
    """
    if len(sentences) != len(durations):
        raise ValueError(
            f"sentences({len(sentences)}) 與 durations({len(durations)}) 長度不符"
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    blocks: list[str] = []
    current_time = 0.0
    for idx, (sent, dur) in enumerate(zip(sentences, durations, strict=True), start=1):
        start_ts = format_srt_timestamp(current_time)
        end_ts = format_srt_timestamp(current_time + dur)
        blocks.append(f"{idx}\n{start_ts} --> {end_ts}\n{sent}\n")
        current_time += dur

    content = "\n".join(blocks)
    output_path.write_text(content, encoding=encoding)
    logger.info("SRT 已寫入: %s (%d 句)", output_path, len(sentences))


def build_srt_string(
    sentences: list[str],
    durations: list[float],
) -> str:
    """將句子與對應時長組裝為 SRT 格式字串（不寫入檔案）。

    Args:
        sentences: 句子列表
        durations: 各句時長（秒）

    Returns:
        SRT 格式字串
    """
    if len(sentences) != len(durations):
        raise ValueError(
            f"sentences({len(sentences)}) 與 durations({len(durations)}) 長度不符"
        )

    blocks: list[str] = []
    current_time = 0.0
    for idx, (sent, dur) in enumerate(zip(sentences, durations, strict=True), start=1):
        start_ts = format_srt_timestamp(current_time)
        end_ts = format_srt_timestamp(current_time + dur)
        blocks.append(f"{idx}\n{start_ts} --> {end_ts}\n{sent}\n")
        current_time += dur

    return "\n".join(blocks)


# ---------------------------------------------------------------------------
# 高階便利函式
# ---------------------------------------------------------------------------


def generate_srt(
    text: str,
    total_duration: float,
    mode: str = "uniform",
    secondary_split: bool = False,
    max_length: int = 100,
    zh_cpm: int = 160,
    en_wpm: int = 150,
) -> str:
    """一站式 SRT 生成（回傳字串，不寫檔）。

    Args:
        text: 原始文字（會自動 normalize）
        total_duration: 音訊總時長（秒）
        mode: "uniform"（Mode A）或 "rate"（Mode B）
        secondary_split: 是否啟用次要斷句
        max_length: 次要斷句的最大字元長度
        zh_cpm: 中文速率（字/分鐘）
        en_wpm: 英文速率（字/分鐘）

    Returns:
        SRT 格式字串；若無有效句子則回傳空字串
    """
    text = normalize_text(text)
    sentences = split_sentences(text, secondary_split=secondary_split, max_length=max_length)
    if not sentences:
        return ""

    if mode == "rate":
        durations = allocate_rate_based_durations(sentences, total_duration, zh_cpm, en_wpm)
    else:
        durations = allocate_uniform_durations(sentences, total_duration)

    return build_srt_string(sentences, durations)


def generate_srt_file(
    text: str,
    total_duration: float,
    output_path: str | Path,
    mode: str = "uniform",
    secondary_split: bool = False,
    max_length: int = 100,
    zh_cpm: int = 160,
    en_wpm: int = 150,
) -> Path:
    """一站式 SRT 生成並寫入檔案。

    Args:
        text: 原始文字（會自動 normalize）
        total_duration: 音訊總時長（秒）
        output_path: 輸出路徑（.srt）
        mode: "uniform" 或 "rate"
        secondary_split: 是否啟用次要斷句
        max_length: 次要斷句的最大字元長度
        zh_cpm: 中文速率（字/分鐘）
        en_wpm: 英文速率（字/分鐘）

    Returns:
        寫入的 Path 物件
    """
    srt_content = generate_srt(
        text=text,
        total_duration=total_duration,
        mode=mode,
        secondary_split=secondary_split,
        max_length=max_length,
        zh_cpm=zh_cpm,
        en_wpm=en_wpm,
    )
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(srt_content, encoding="utf-8")
    logger.info("SRT 已寫入: %s", output_path)
    return output_path
