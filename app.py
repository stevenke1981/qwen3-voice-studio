"""Qwen3 Voice Studio — 主程式進入點.

Usage:
    python app.py            # 啟動 GUI (port 7860)
    python app.py --port 8080
    python app.py --share      # 建立 Gradio share link
    python app.py --demo       # Demo 模式（不載入模型）
"""

from __future__ import annotations

import argparse
import logging
import sys


class _SuppressSoX(logging.Filter):
    """Suppress the 'SoX could not be found' warning from librosa.

    SoX is an optional backend for librosa; its absence does not affect
    qwen-tts inference in any way.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return "SoX could not be found" not in record.getMessage()


class _SuppressWin10054(logging.Filter):
    """Suppress the harmless WinError 10054 asyncio noise on Windows.

    When a browser disconnects, Windows ProactorBasePipeTransport tries to
    shut down the socket after the remote side already closed it, which raises
    ConnectionResetError [WinError 10054]. This is not an application error.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return not (
            record.name == "asyncio"
            and record.levelno == logging.ERROR
            and "WinError 10054" in (record.getMessage())
        )


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

if sys.platform == "win32":
    logging.getLogger("asyncio").addFilter(_SuppressWin10054())

logging.getLogger("sox").addFilter(_SuppressSoX())

logger = logging.getLogger("qwen3-voice-studio")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Qwen3 Voice Studio")
    parser.add_argument("--port", type=int, default=7860, help="Gradio UI port")
    parser.add_argument("--share", action="store_true", help="建立 Gradio share link")
    parser.add_argument("--demo", action="store_true", help="Demo 模式（不載入任何模型）")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # ── 載入設定 ──────────────────────────────────────────────────────────
    from src.config import AppSettings

    settings = AppSettings.load()

    # ── 初始化後端元件 ──────────────────────────────────────────────────────
    from src.error_handler import ErrorHandler
    from src.history import HistoryManager
    from src.multi_engine import ModelPool
    from src.voice_library import VoiceLibrary

    error_handler = ErrorHandler()
    history_mgr   = HistoryManager()
    voice_lib      = VoiceLibrary()

    model_pool = ModelPool(
        custom_voice_path=settings.tts.custom_voice_model,
        voice_design_path=settings.tts.voice_design_model,
        base_path=settings.tts.base_model,
        device=settings.tts.device,
    )

    # ── 預先載入 Base 模型（非 demo 模式） ──────────────────────────────────
    if not args.demo and settings.tts.auto_start:
        logger.info("預先載入 Base 模型（聲音克隆）...")
        try:
            model_pool.get("base")
            logger.info("Base 模型載入完成")
        except Exception as e:
            logger.warning("Base 模型載入失敗（應用仍可啟動，使用時再試）: %s", e)
            error_handler.add_error("ModelPool", str(e))
    else:
        logger.info("Demo 模式 — 跳過模型載入")

    # ── 建構 Gradio UI ──────────────────────────────────────────────────────
    from gui.app_ui import _APP_CSS, _APP_THEME, build_app

    app = build_app(
        model_pool=model_pool,
        voice_lib=voice_lib,
        history_mgr=history_mgr,
        error_handler=error_handler,
        settings=settings,
        default_locale=settings.locale,
    )

    app.queue(default_concurrency_limit=4)

    logger.info("啟動 Gradio UI: http://127.0.0.1:%d", args.port)
    app.launch(
        server_name="127.0.0.1",
        server_port=args.port,
        share=args.share,
        show_error=True,
        theme=_APP_THEME,
        css=_APP_CSS,
    )


if __name__ == "__main__":
    main()
