"""Qwen3 Voice Studio — TTS 引擎封裝.

每個 TTSEngine 實例只包裝一個模型。
- model_type == "custom_voice" → synthesize() 使用 generate_custom_voice
- model_type == "voice_design" → voice_design() 使用 generate_voice_design
- model_type == "base"         → voice_clone() 使用 generate_voice_clone
"""

from __future__ import annotations

import io
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TTSResult:
    """TTS 合成結果."""

    audio: np.ndarray
    sample_rate: int
    duration: float
    latency_ms: float
    speaker: str
    language: str
    text: str


@dataclass
class TTSEngine:
    """Qwen3-TTS 單一模型引擎封裝."""

    model_path: str = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
    device: str = "cuda:0"
    _model: Any = field(default=None, repr=False)
    _loaded: bool = False
    _model_type: str = ""  # 載入後由 qwen_tts 物件決定

    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def model_type(self) -> str:
        """已載入模型的 tts_model_type (custom_voice / voice_design / base)."""
        return self._model_type

    def load_model(self) -> None:
        """載入 TTS 模型並偵測 model_type."""
        if self._loaded:
            return
        try:
            import torch
            from qwen_tts import Qwen3TTSModel

            logger.info("Loading TTS model: %s on %s", self.model_path, self.device)
            self._model = Qwen3TTSModel.from_pretrained(
                self.model_path,
                device_map=self.device,
                dtype=torch.bfloat16,
            )
            self._model_type = getattr(self._model.model, "tts_model_type", "base")
            self._loaded = True
            logger.info("TTS model loaded: %s (type=%s)", self.model_path, self._model_type)
        except ImportError:
            logger.warning("qwen-tts not installed — running in demo mode.")
            self._loaded = False
        except Exception as e:
            logger.error("Failed to load TTS model: %s", e)
            raise

    # ── 核心合成方法 ────────────────────────────────────────────────────────

    def synthesize(
        self,
        text: str,
        speaker: str = "Vivian",
        language: str = "Chinese",
        instruct: str = "",
    ) -> TTSResult:
        """Custom Voice 模式：具名音色合成.

        需要 model_type == "custom_voice"。
        未載入模型時返回靜音（demo 模式）。
        """
        start = time.perf_counter()

        if self._model is not None and self._loaded:
            if self._model_type != "custom_voice":
                raise RuntimeError(
                    f"synthesize() 需要 custom_voice 模型，目前載入的是 '{self._model_type}'。"
                    f"\n請在設定中指定 CustomVoice 模型路徑。"
                )
            kwargs: dict[str, Any] = {
                "text": text,
                "language": language.lower(),
                "speaker": speaker,
            }
            if instruct:
                kwargs["instruct"] = instruct
            wavs, sr = self._model.generate_custom_voice(**kwargs)
            audio = wavs[0] if isinstance(wavs, list) else wavs
            if not isinstance(audio, np.ndarray):
                audio = np.array(audio, dtype=np.float32)
        else:
            sr = 24000
            audio = np.zeros(int(sr * max(1.0, len(text) * 0.15)), dtype=np.float32)

        elapsed = (time.perf_counter() - start) * 1000
        return TTSResult(
            audio=audio, sample_rate=sr,
            duration=len(audio) / sr if sr > 0 else 0.0,
            latency_ms=elapsed, speaker=speaker, language=language, text=text,
        )

    def voice_design(
        self,
        text: str,
        language: str = "Chinese",
        instruct: str = "",
    ) -> TTSResult:
        """Voice Design 模式：用描述文字生成音色.

        需要 model_type == "voice_design"。
        """
        start = time.perf_counter()

        if self._model is not None and self._loaded:
            if self._model_type != "voice_design":
                raise RuntimeError(
                    f"voice_design() 需要 voice_design 模型，目前載入的是 '{self._model_type}'。"
                )
            wavs, sr = self._model.generate_voice_design(
                text=text,
                language=language.lower(),
                instruct=instruct,
            )
            audio = wavs[0] if isinstance(wavs, list) else wavs
            if not isinstance(audio, np.ndarray):
                audio = np.array(audio, dtype=np.float32)
        else:
            sr = 24000
            audio = np.zeros(int(sr * max(1.0, len(text) * 0.15)), dtype=np.float32)

        elapsed = (time.perf_counter() - start) * 1000
        return TTSResult(
            audio=audio, sample_rate=sr,
            duration=len(audio) / sr if sr > 0 else 0.0,
            latency_ms=elapsed, speaker="design", language=language, text=text,
        )

    def voice_clone(
        self,
        text: str,
        language: str = "Chinese",
        ref_audio: Any = None,
        ref_text: str = "",
        x_vector_only: bool = False,
    ) -> TTSResult:
        """Voice Clone 模式：以參考音頻克隆音色.

        需要 model_type == "base"。
        ref_audio: (np.ndarray, sample_rate) tuple 或 wav 路徑。
        """
        start = time.perf_counter()

        if self._model is not None and self._loaded:
            if self._model_type != "base":
                raise RuntimeError(
                    f"voice_clone() 需要 base 模型，目前載入的是 '{self._model_type}'。"
                )
            if ref_audio is None:
                raise ValueError("voice_clone() 需要提供 ref_audio 參考音頻。")

            kwargs: dict[str, Any] = {
                "text": text,
                "language": language.lower(),
                "ref_audio": ref_audio,
                "x_vector_only_mode": x_vector_only,
            }
            if ref_text and not x_vector_only:
                kwargs["ref_text"] = ref_text

            wavs, sr = self._model.generate_voice_clone(**kwargs)
            audio = wavs[0] if isinstance(wavs, list) else wavs
            if not isinstance(audio, np.ndarray):
                audio = np.array(audio, dtype=np.float32)
        else:
            sr = 24000
            audio = np.zeros(int(sr * max(1.0, len(text) * 0.15)), dtype=np.float32)

        elapsed = (time.perf_counter() - start) * 1000
        return TTSResult(
            audio=audio, sample_rate=sr,
            duration=len(audio) / sr if sr > 0 else 0.0,
            latency_ms=elapsed, speaker="clone", language=language, text=text,
        )

    # ── 工具方法 ────────────────────────────────────────────────────────────

    def to_wav_bytes(self, result: TTSResult) -> bytes:
        """將 TTSResult 轉為 WAV bytes."""
        import soundfile as sf

        buf = io.BytesIO()
        sf.write(buf, result.audio, result.sample_rate, format="WAV")
        buf.seek(0)
        return buf.read()

    def get_supported_speakers(self) -> list[str]:
        """取得此模型支援的說話者列表（custom_voice 模型適用）."""
        if self._model and callable(getattr(self._model.model, "get_supported_speakers", None)):
            raw = self._model.model.get_supported_speakers()
            return list(raw) if raw else []
        return []

    def get_supported_languages(self) -> list[str]:
        """取得此模型支援的語言列表."""
        if self._model and callable(getattr(self._model.model, "get_supported_languages", None)):
            raw = self._model.model.get_supported_languages()
            return [l.capitalize() for l in raw] if raw else []
        return []

    def unload(self) -> None:
        """卸載模型釋放記憶體."""
        self._model = None
        self._loaded = False
        self._model_type = ""
        logger.info("TTS model unloaded: %s", self.model_path)
