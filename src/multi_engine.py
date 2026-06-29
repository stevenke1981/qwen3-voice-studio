"""Qwen3 Voice Studio — 多模型池.

ModelPool 管理三種模型的懶載入：
  "custom_voice" → generate_custom_voice  (具名音色)
  "voice_design" → generate_voice_design  (描述音色)
  "base"         → generate_voice_clone   (聲音克隆)

使用方式：
    pool = ModelPool(settings.tts)
    engine = pool.get("base")          # 懶載入後回傳 TTSEngine
    result = engine.voice_clone(...)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from src.tts_engine import TTSEngine

logger = logging.getLogger(__name__)


@dataclass
class ModelPool:
    """懶載入 + 管理多個 TTSEngine 實例."""

    custom_voice_path: str = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
    voice_design_path: str = "Qwen/Qwen3-TTS-12Hz-0.6B-VoiceDesign"
    base_path:         str = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
    device:            str = "cuda:0"

    _engines: dict[str, TTSEngine] = field(default_factory=dict, repr=False)

    # 三種 model_type 對應的路徑 key
    _PATH_MAP: dict[str, str] = field(
        default_factory=lambda: {
            "custom_voice": "custom_voice_path",
            "voice_design": "voice_design_path",
            "base":         "base_path",
        },
        repr=False,
    )

    def get(self, kind: str) -> TTSEngine:
        """回傳指定 kind 的引擎，首次呼叫時自動下載並載入模型.

        Args:
            kind: "custom_voice" | "voice_design" | "base"

        Returns:
            已載入的 TTSEngine

        Raises:
            ValueError: 不支援的 kind
            RuntimeError: 模型無法下載且本地不存在
        """
        if kind not in ("custom_voice", "voice_design", "base"):
            raise ValueError(f"不支援的模型類型: {kind!r}，請使用 custom_voice / voice_design / base")

        if kind not in self._engines:
            path_attr = self._PATH_MAP[kind]
            model_path = getattr(self, path_attr)
            logger.info("ModelPool: 載入 %s 模型 %s", kind, model_path)
            engine = TTSEngine(model_path=model_path, device=self.device)

            # 先確保模型可用，下載失敗會拋出具體異常
            self._ensure_downloaded(model_path)

            engine.load_model()
            self._engines[kind] = engine
            logger.info("ModelPool: %s 已就緒", kind)

        return self._engines[kind]

    def _ensure_downloaded(self, model_path: str) -> None:
        """確保模型已下載到本地快取。

        Raises:
            RuntimeError: 模型無法取得（非 HF 模型路徑且非本地存在）
        """
        from src.model_manager import ensure_tts_model_available

        # 如果是本地路徑不需要下載
        if Path(model_path).exists():
            return

        try:
            ensure_tts_model_available(model_path)
        except Exception as e:
            logger.error("模型下載失敗: %s", e)
            # 檢查 HF 快取是否有此模型
            if not _is_model_in_hf_cache(model_path):
                raise RuntimeError(
                    f"模型 {model_path} 無法下載且本地不存在。"
                    f"請檢查網路連線或手動下載後指定本地路徑。"
                ) from e
            logger.warning("模型從 HF 快取載入（下載曾有問題但快取存在）: %s", model_path)


    def is_loaded(self, kind: str) -> bool:
        """檢查指定 kind 是否已載入."""
        engine = self._engines.get(kind)
        return engine is not None and engine.is_loaded()

    def loaded_kinds(self) -> list[str]:
        """回傳已載入的 model kind 列表."""
        return [k for k, e in self._engines.items() if e.is_loaded()]

    def unload(self, kind: str) -> None:
        """卸載指定 kind 的模型，釋放 VRAM."""
        if kind in self._engines:
            self._engines[kind].unload()
            del self._engines[kind]
            logger.info("ModelPool: %s 已卸載", kind)

    def unload_all(self) -> None:
        """卸載所有已載入的模型."""
        for k in list(self._engines.keys()):
            self.unload(k)


def _is_model_in_hf_cache(repo_id: str) -> bool:
    """檢查 HuggingFace 快取中是否有指定 repo_id。"""
    try:
        from huggingface_hub import scan_cache_dir

        cache_info = scan_cache_dir()
        for repo in cache_info.repos:
            if repo.repo_id == repo_id:
                return True
    except Exception:
        pass
    return False
