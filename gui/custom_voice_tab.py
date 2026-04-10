"""Qwen3 Voice Studio — Custom Voice 分頁.

使用 CustomVoice 模型（Qwen3-TTS-12Hz-0.6B-CustomVoice）：
  - 從內建音色庫選擇說話者
  - 支援語言與風格指令
  - 輸出 WAV + 可選 SRT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import gradio as gr

from src.audio_utils import to_gradio_audio
from src.config import BUILTIN_SPEAKERS, SUPPORTED_TTS_LANGUAGES
from src.i18n import t
from utils.srt_generator import generate_srt

if TYPE_CHECKING:
    from src.error_handler import ErrorHandler
    from src.history import HistoryManager
    from src.multi_engine import ModelPool


def _synthesize(
    text: str,
    speaker: str,
    language: str,
    instruct: str,
    srt_mode: str,
    locale: str,
    model_pool: ModelPool | None,
    history_mgr: HistoryManager | None,
    error_handler: ErrorHandler | None,
) -> tuple[Any, str, str]:
    if not text.strip():
        return None, "", t("error_empty_text", locale)
    if model_pool is None:
        return None, "", t("error_model_not_loaded", locale)

    try:
        engine = model_pool.get("custom_voice")
        result = engine.synthesize(text=text, speaker=speaker, language=language, instruct=instruct)
        audio_out = to_gradio_audio(result.audio, result.sample_rate)

        srt_text = ""
        if srt_mode != "none":
            srt_text = generate_srt(text=text, total_duration=result.duration, mode=srt_mode)

        if history_mgr:
            history_mgr.add_record(
                text_preview=text[:80], full_text=text,
                speaker=speaker, language=language, duration=result.duration,
            )

        status = t("status_synthesis_done", locale).format(
            duration=f"{result.duration:.1f}", latency=f"{result.latency_ms:.0f}",
        )
        return audio_out, srt_text, status

    except Exception as e:
        if error_handler:
            error_handler.add_error("CustomVoice", str(e))
        return None, "", f"❌ {e}"


def build_custom_voice_tab(
    model_pool: ModelPool | None,
    history_mgr: HistoryManager | None,
    error_handler: ErrorHandler | None,
    locale_state: gr.State,
) -> dict[str, Any]:
    """Custom Voice 分頁."""
    components: dict[str, Any] = {}

    with gr.Tab("🎙️ Custom Voice") as tab:
        components["tab_custom_voice"] = tab

        gr.Markdown(
            "**具名音色合成** — 從內建音色庫選擇說話者，搭配語言與風格指令生成語音。\n\n"
            "模型：`Qwen3-TTS-12Hz-0.6B-CustomVoice`"
        )

        with gr.Row():
            with gr.Column(scale=3):
                text_input = gr.Textbox(
                    label=t("tts_input_text", "zh-TW"),
                    placeholder=t("tts_placeholder", "zh-TW"),
                    lines=6, max_lines=20,
                )
                components["cv_text"] = text_input

            with gr.Column(scale=1):
                speaker_dd = gr.Dropdown(
                    choices=BUILTIN_SPEAKERS, value="Vivian",
                    label=t("tts_speaker", "zh-TW"),
                )
                components["cv_speaker"] = speaker_dd

                language_dd = gr.Dropdown(
                    choices=SUPPORTED_TTS_LANGUAGES, value="Chinese",
                    label=t("tts_language", "zh-TW"),
                )
                components["cv_language"] = language_dd

                instruct_input = gr.Textbox(
                    label=t("tts_instruct", "zh-TW"),
                    placeholder=t("tts_instruct_placeholder", "zh-TW"),
                    lines=2,
                )
                components["cv_instruct"] = instruct_input

                srt_mode_dd = gr.Dropdown(
                    choices=["none", "uniform", "rate"], value="uniform",
                    label=t("tts_srt_mode", "zh-TW"),
                )
                components["cv_srt_mode"] = srt_mode_dd

        synth_btn = gr.Button(t("tts_synthesize", "zh-TW"), variant="primary", size="lg")
        components["cv_synthesize"] = synth_btn

        with gr.Row():
            with gr.Column():
                audio_out = gr.Audio(label=t("tts_audio_output", "zh-TW"), type="numpy")
                components["cv_audio_output"] = audio_out
            with gr.Column():
                srt_out = gr.Textbox(
                    label=t("tts_srt_output", "zh-TW"), lines=10, interactive=False,
                )
                components["cv_srt_output"] = srt_out

        status_out = gr.Textbox(label=t("tts_status", "zh-TW"), interactive=False, max_lines=2)
        components["cv_status"] = status_out

        synth_btn.click(
            fn=lambda txt, spk, lang, inst, srt_m, loc: _synthesize(
                txt, spk, lang, inst, srt_m, loc,
                model_pool, history_mgr, error_handler,
            ),
            inputs=[text_input, speaker_dd, language_dd, instruct_input, srt_mode_dd, locale_state],
            outputs=[audio_out, srt_out, status_out],
        )

    return components
