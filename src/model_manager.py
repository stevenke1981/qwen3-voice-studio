"""Qwen3 Voice Studio — 模型自動下載與管理."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_CACHE_DIR = Path.home() / ".cache" / "qwen3-voice-studio"


def get_cache_dir() -> Path:
    """取得模型快取目錄."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR


def is_model_downloaded(repo_id: str) -> bool:
    """檢查模型是否已下載至本地."""
    try:
        from huggingface_hub import scan_cache_dir

        cache_info = scan_cache_dir()
        for repo in cache_info.repos:
            if repo.repo_id == repo_id:
                return True
    except Exception:
        pass

    # 也檢查是否為本地路徑
    return Path(repo_id).exists()


def download_model(repo_id: str, revision: str = "main") -> str:
    """下載 HuggingFace 模型.

    Args:
        repo_id: HuggingFace 模型 ID (e.g. Qwen/Qwen3-TTS-0.6B)
        revision: 版本

    Returns:
        本地快取路徑
    """
    try:
        from huggingface_hub import snapshot_download

        logger.info("Downloading model: %s", repo_id)
        local_path = snapshot_download(
            repo_id=repo_id,
            revision=revision,
            cache_dir=str(get_cache_dir()),
        )
        logger.info("Model downloaded to: %s", local_path)
        return local_path
    except ImportError as exc:
        raise RuntimeError(
            "huggingface-hub is required. Run: pip install huggingface-hub"
        ) from exc
    except Exception as e:
        logger.error("Failed to download model %s: %s", repo_id, e)
        raise


def ensure_tts_model_available(
    tts_model: str = "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
) -> str:  # noqa: E501
    """確保 TTS 模型可用.

    Returns:
        本地模型路徑字串
    """
    if Path(tts_model).exists():
        logger.info("Using local model: %s", tts_model)
        return tts_model
    elif is_model_downloaded(tts_model):
        logger.info("Model already cached: %s", tts_model)
        return tts_model
    else:
        logger.info("Model not found locally, downloading: %s", tts_model)
        return download_model(tts_model)
