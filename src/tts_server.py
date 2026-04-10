"""Qwen3 Voice Studio — FastAPI TTS 本地伺服器."""

from __future__ import annotations

import logging
import threading
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from src.config import BUILTIN_SPEAKERS, SUPPORTED_TTS_LANGUAGES
from src.tts_engine import TTSEngine
from utils.srt_generator import generate_srt as _generate_srt

logger = logging.getLogger(__name__)


# ── Request / Response Models ─────────────────────────────
class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)
    speaker: str = Field(default="Vivian")
    language: str = Field(default="Chinese")
    instruct: str = Field(default="")


class SRTRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)
    speaker: str = Field(default="Vivian")
    language: str = Field(default="Chinese")
    instruct: str = Field(default="")
    srt_mode: str = Field(default="uniform", description="uniform | rate")
    zh_cpm: int = Field(default=160, ge=60, le=600)
    en_wpm: int = Field(default=150, ge=60, le=400)


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


class MetricsResponse(BaseModel):
    gpu_name: str = "N/A"
    gpu_utilization: float = 0.0
    gpu_memory_used_mb: float = 0.0
    gpu_memory_total_mb: float = 0.0
    model_loaded: bool = False
    last_latency_ms: float = 0.0


# ── App Factory ──────────────────────────────────────────
def create_app(
    tts_engine: TTSEngine | None = None,
) -> FastAPI:
    """建立 FastAPI app."""
    app = FastAPI(title="Qwen3 Voice Studio TTS Server", version="1.0.0")
    _state: dict[str, Any] = {
        "tts": tts_engine,
        "last_latency": 0.0,
    }

    @app.get("/tts/health")
    async def health() -> HealthResponse:
        tts = _state["tts"]
        return HealthResponse(
            status="ok",
            model_loaded=tts.is_loaded() if tts else False,
        )

    @app.get("/tts/voices")
    async def voices() -> dict[str, list[str]]:
        return {
            "speakers": BUILTIN_SPEAKERS,
            "languages": SUPPORTED_TTS_LANGUAGES,
        }

    @app.post("/tts/synthesize")
    async def synthesize(req: SynthesizeRequest) -> Response:
        tts = _state["tts"]
        if not tts:
            raise HTTPException(503, "TTS engine not available")
        result = tts.synthesize(
            text=req.text,
            speaker=req.speaker,
            language=req.language,
            instruct=req.instruct,
        )
        _state["last_latency"] = result.latency_ms
        wav_bytes = tts.to_wav_bytes(result)
        return Response(
            content=wav_bytes,
            media_type="audio/wav",
            headers={"X-Latency-Ms": str(result.latency_ms)},
        )

    @app.post("/tts/srt")
    async def generate_srt_endpoint(req: SRTRequest) -> dict[str, str]:
        tts = _state["tts"]
        if not tts:
            raise HTTPException(503, "TTS engine not available")

        result = tts.synthesize(
            text=req.text,
            speaker=req.speaker,
            language=req.language,
            instruct=req.instruct,
        )
        _state["last_latency"] = result.latency_ms

        srt_text = _generate_srt(
            text=req.text,
            total_duration=result.duration,
            mode=req.srt_mode,
            zh_cpm=req.zh_cpm,
            en_wpm=req.en_wpm,
        )
        return {"srt": srt_text}

    @app.get("/tts/metrics")
    async def metrics() -> MetricsResponse:
        from src.monitor import get_system_metrics

        tts = _state["tts"]
        m = get_system_metrics(
            model_loaded=tts.is_loaded() if tts else False,
            last_latency=_state["last_latency"],
        )
        return MetricsResponse(
            gpu_name=m.gpu_name,
            gpu_utilization=m.gpu_utilization,
            gpu_memory_used_mb=m.gpu_memory_used_mb,
            gpu_memory_total_mb=m.gpu_memory_total_mb,
            model_loaded=m.model_loaded,
            last_latency_ms=m.last_latency_ms,
        )

    return app


# ── Server Manager ───────────────────────────────────────
class TTSServerManager:
    """管理 TTS FastAPI 伺服器生命週期."""

    def __init__(
        self,
        tts_engine: TTSEngine | None = None,
        port: int = 8990,
    ) -> None:
        self._tts = tts_engine
        self._port = port
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """在背景 thread 啟動伺服器."""
        if self._running:
            return
        app = create_app(self._tts)
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=self._port,
            log_level="warning",
        )
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()
        self._running = True
        logger.info("TTS server started on port %d", self._port)

    def _run_server(self) -> None:
        if self._server:
            self._server.run()
        self._running = False

    def stop(self) -> None:
        """停止伺服器."""
        if self._server:
            self._server.should_exit = True
        self._running = False
        logger.info("TTS server stopped")
