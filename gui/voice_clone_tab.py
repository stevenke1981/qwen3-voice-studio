"""Qwen3 Voice Studio — Voice Clone 分頁.

使用 Base 模型（Qwen3-TTS-12Hz-0.6B-Base）：
  - 上傳參考音頻（WAV/MP3）
  - 可選提供參考文字（ICL 模式，品質更佳）
  - 以克隆音色合成新文字
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import gradio as gr
import numpy as np

from src.audio_utils import to_gradio_audio
from src.config import SUPPORTED_TTS_LANGUAGES
from src.i18n import t

if TYPE_CHECKING:
    from src.error_handler import ErrorHandler
    from src.multi_engine import ModelPool


def _load_ref_audio(audio_file: Any) -> tuple[np.ndarray, int] | None:
    """從 Gradio file 物件讀取參考音頻."""
    if audio_file is None:
        return None
    import soundfile as sf
    path = audio_file.name if hasattr(audio_file, "name") else str(audio_file)
    data, sr = sf.read(path, dtype="float32")
    if data.ndim > 1:
        data = data.mean(axis=1)
    return data, sr


def _clone(
    text: str,
    ref_audio_file: Any,
    ref_text: str,
    language: str,
    x_vector_only: bool,
    locale: str,
    model_pool: ModelPool | None,
    error_handler: Any | None,
) -> tuple[Any, str]:
    if not text.strip():
        return None, t("error_empty_text", locale)
    if ref_audio_file is None:
        return None, "❌ 請上傳參考音頻"
    if model_pool is None:
        return None, t("error_model_not_loaded", locale)

    try:
        ref = _load_ref_audio(ref_audio_file)
        if ref is None:
            return None, "❌ 無法讀取參考音頻"

        engine = model_pool.get("base")
        result = engine.voice_clone(
            text=text,
            language=language,
            ref_audio=ref,
            ref_text=ref_text.strip() or None,
            x_vector_only=x_vector_only,
        )
        audio_out = to_gradio_audio(result.audio, result.sample_rate)
        status = f"✅ 克隆完成  時長 {result.duration:.1f}s  延遲 {result.latency_ms:.0f}ms"
        return audio_out, status

    except Exception as e:
        if error_handler:
            error_handler.add_error("VoiceClone", str(e))
        return None, f"❌ {e}"


def build_voice_clone_tab(
    model_pool: ModelPool | None,
    error_handler: Any | None,
    locale_state: gr.State,
) -> dict[str, Any]:
    """Voice Clone 分頁."""
    components: dict[str, Any] = {}

    with gr.Tab("🔁 Voice Clone") as tab:
        components["tab_voice_clone"] = tab

        gr.Markdown(
            "**聲音克隆** — 上傳參考音頻（3–10 秒效果最佳），模型將克隆該音色並合成新文字。\n\n"
            "模型：`Qwen3-TTS-12Hz-0.6B-Base`  |  "
            "提供參考文字可使用 ICL 模式，品質通常更佳。"
        )

        with gr.Row():
            with gr.Column(scale=2):
                text_input = gr.Textbox(
                    label="合成文字",
                    placeholder="輸入要合成的文字內容...",
                    value="這是聲音克隆測試，模型將模仿參考音頻中的說話風格。",
                    lines=5,
                )
                components["vc_text"] = text_input

                language_dd = gr.Dropdown(
                    choices=SUPPORTED_TTS_LANGUAGES, value="Chinese",
                    label="語言",
                )
                components["vc_language"] = language_dd

            with gr.Column(scale=2):
                ref_audio_input = gr.File(
                    label="參考音頻（WAV / MP3，建議 3–10 秒）",
                    file_types=[".wav", ".mp3", ".flac", ".ogg"],
                )
                components["vc_ref_audio"] = ref_audio_input

                ref_text_input = gr.Textbox(
                    label="參考文字（選填，用於 ICL 模式）",
                    placeholder="若知道參考音頻的文字內容，填入此欄可提升品質...",
                    lines=3,
                )
                components["vc_ref_text"] = ref_text_input

                x_vector_chk = gr.Checkbox(
                    label="X-Vector Only 模式（只使用音色特徵，忽略參考文字）",
                    value=False,
                )
                components["vc_xvector"] = x_vector_chk

        clone_btn = gr.Button("🔁 克隆語音", variant="primary", size="lg")
        components["vc_clone"] = clone_btn

        audio_out = gr.Audio(label="克隆音訊", type="numpy")
        components["vc_audio"] = audio_out

        status_out = gr.Textbox(label="狀態", interactive=False, max_lines=2)
        components["vc_status"] = status_out

        clone_btn.click(
            fn=lambda txt, ref, rtext, lang, xv, loc: _clone(
                txt, ref, rtext, lang, xv, loc, model_pool, error_handler,
            ),
            inputs=[text_input, ref_audio_input, ref_text_input, language_dd, x_vector_chk, locale_state],
            outputs=[audio_out, status_out],
        )

    return components
