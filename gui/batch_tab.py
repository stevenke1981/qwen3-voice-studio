"""Qwen3 Voice Studio — 批次合成分頁."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

import gradio as gr

from src.audio_utils import read_text_file, split_text_to_sentences
from src.config import BUILTIN_SPEAKERS, SUPPORTED_TTS_LANGUAGES
from src.i18n import t
from utils.srt_generator import generate_srt

if TYPE_CHECKING:
    from src.error_handler import ErrorHandler
    from src.multi_engine import ModelPool


def _run_batch(
    file_obj: Any,
    speaker: str,
    language: str,
    instruct: str,
    srt_mode: str,
    locale: str,
    model_pool: ModelPool | None,
    error_handler: ErrorHandler | None,
) -> tuple[str, list[str] | None]:
    """批次處理文字檔（使用 CustomVoice 模型）."""
    if not model_pool:
        return t("error_model_not_loaded", locale), None

    if file_obj is None:
        return t("batch_no_file", locale), None

    try:
        file_path = file_obj.name if hasattr(file_obj, "name") else str(file_obj)
        text = read_text_file(file_path)
        sentences = split_text_to_sentences(text)
        if not sentences:
            return t("batch_empty_file", locale), None

        output_dir = Path(tempfile.mkdtemp(prefix="qwen3_batch_"))
        results: list[str] = []
        total = len(sentences)

        engine = model_pool.get("custom_voice")
        for idx, sentence in enumerate(sentences, 1):
            result = engine.synthesize(
                text=sentence,
                speaker=speaker,
                language=language,
                instruct=instruct,
            )
            wav_bytes = engine.to_wav_bytes(result)
            out_file = output_dir / f"{idx:04d}.wav"
            out_file.write_bytes(wav_bytes)
            results.append(str(out_file))

            if srt_mode != "none":
                srt_text = generate_srt(
                    text=sentence,
                    total_duration=result.duration,
                    mode=srt_mode,
                )
                srt_file = output_dir / f"{idx:04d}.srt"
                srt_file.write_text(srt_text, encoding="utf-8")

        status = t("batch_done", locale).format(count=total, path=str(output_dir))
        return status, results

    except Exception as e:
        if error_handler:
            error_handler.add_error("Batch", str(e))
        return f"❌ {e}", None


def build_batch_tab(
    model_pool: ModelPool | None,
    error_handler: ErrorHandler | None,
    locale_state: gr.State,
) -> dict[str, Any]:
    """建構批次合成分頁."""
    components: dict[str, Any] = {}

    with gr.Tab(t("tab_batch", "zh-TW")) as tab:
        components["tab_batch"] = tab

        gr.Markdown(t("batch_description", "zh-TW"))

        with gr.Row():
            file_input = gr.File(
                label=t("batch_upload", "zh-TW"),
                file_types=[".txt", ".md"],
            )
            components["batch_upload"] = file_input

        with gr.Row():
            speaker_dd = gr.Dropdown(
                choices=BUILTIN_SPEAKERS,
                value="Vivian",
                label=t("tts_speaker", "zh-TW"),
            )

            language_dd = gr.Dropdown(
                choices=SUPPORTED_TTS_LANGUAGES,
                value="Chinese",
                label=t("tts_language", "zh-TW"),
            )

            instruct_input = gr.Textbox(
                label=t("tts_instruct", "zh-TW"),
                lines=1,
            )

            srt_mode_dd = gr.Dropdown(
                choices=["none", "uniform", "rate"],
                value="uniform",
                label=t("tts_srt_mode", "zh-TW"),
            )

        batch_btn = gr.Button(
            t("batch_start", "zh-TW"),
            variant="primary",
        )
        components["batch_start"] = batch_btn

        batch_status = gr.Textbox(
            label=t("batch_status", "zh-TW"),
            interactive=False,
            lines=3,
        )
        components["batch_status"] = batch_status

        batch_output = gr.File(
            label=t("batch_output", "zh-TW"),
            visible=False,
        )

        batch_btn.click(
            fn=lambda f, spk, lang, inst, srt_m, loc: _run_batch(
                f, spk, lang, inst, srt_m, loc,
                model_pool, error_handler,
            ),
            inputs=[file_input, speaker_dd, language_dd, instruct_input, srt_mode_dd, locale_state],
            outputs=[batch_status, batch_output],
        )

    return components
