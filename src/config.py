"""Qwen3 Voice Studio — 應用程式設定管理."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

_CONFIG_DIR = Path.home() / ".qwen3-voice-studio"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

# ── 模型 ID 常數 ──────────────────────────────────────────────────────────────
MODEL_CUSTOM_VOICE  = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
MODEL_VOICE_DESIGN  = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"   # 0.6B 無此型號
MODEL_BASE          = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"

# 1.7B 大模型（高品質，需更多 VRAM）
MODEL_CUSTOM_VOICE_LG = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
MODEL_VOICE_DESIGN_LG = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
MODEL_BASE_LG         = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"

ALL_MODEL_IDS = [
    MODEL_CUSTOM_VOICE,   # 0.6B
    MODEL_BASE,           # 0.6B
    MODEL_VOICE_DESIGN,   # 1.7B（0.6B 無此型號）
    MODEL_CUSTOM_VOICE_LG,
    MODEL_VOICE_DESIGN_LG,
    MODEL_BASE_LG,
]

DEFAULT_DEVICE = "cuda:0"  # GPU 推論預設；無 GPU 時改為 "cpu"
DEFAULT_PORT   = 8990

BUILTIN_SPEAKERS = [
    "Vivian",
    "Serena",
    "Uncle_Fu",
    "Dylan",
    "Eric",
    "Ryan",
    "Aiden",
    "Ono_Anna",
    "Sohee",
]

SUPPORTED_TTS_LANGUAGES = [
    "Chinese",
    "English",
    "Japanese",
    "Korean",
    "German",
    "French",
    "Russian",
    "Portuguese",
    "Spanish",
    "Italian",
]


class TTSSettings(BaseModel):
    """TTS 多模型設定."""

    # 三種模型各自的路徑（可換成本地路徑）
    custom_voice_model: str = Field(default=MODEL_CUSTOM_VOICE, description="CustomVoice 模型（具名音色）")
    voice_design_model: str = Field(default=MODEL_VOICE_DESIGN, description="VoiceDesign 模型（描述音色）")
    base_model:         str = Field(default=MODEL_BASE,         description="Base 模型（聲音克隆）")

    device: str = Field(default=DEFAULT_DEVICE, description="運算裝置 cuda:0 / cpu")
    port:   int = Field(default=DEFAULT_PORT, ge=1024, le=65535, description="API server port")

    auto_start:  bool = Field(default=True,      description="啟動時自動載入 Base 模型")
    srt_mode:    str  = Field(default="uniform", description="SRT 時間分配模式 uniform|rate")
    zh_cpm:      int  = Field(default=160, ge=60, le=600, description="中文朗讀速率 字/分鐘")
    en_wpm:      int  = Field(default=150, ge=60, le=400, description="英文朗讀速率 字/分鐘")
    output_dir:  str  = Field(default="",        description="音訊輸出目錄（空字串使用預設）")


class AppSettings(BaseModel):
    """應用程式設定."""

    locale: str = Field(default="zh-TW", description="GUI 語言")
    tts: TTSSettings = Field(default_factory=TTSSettings)

    @classmethod
    def load(cls) -> AppSettings:
        """從檔案載入設定，不存在則使用預設值."""
        if _CONFIG_FILE.exists():
            try:
                data = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
                return cls.model_validate(data)
            except (json.JSONDecodeError, ValueError):
                pass
        return cls()

    def save(self) -> None:
        """儲存設定到檔案."""
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        _CONFIG_FILE.write_text(
            self.model_dump_json(indent=2),
            encoding="utf-8",
        )
