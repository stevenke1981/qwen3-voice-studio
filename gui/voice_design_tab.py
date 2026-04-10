"""Qwen3 Voice Studio — Voice Design 分頁.

使用 VoiceDesign 模型（Qwen3-TTS-12Hz-0.6B-VoiceDesign）：
  - 用自然語言描述想要的音色（e.g. "一位溫柔的女聲，帶有輕微磁性"）
  - 生成對應音色的語音
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import gradio as gr

from src.audio_utils import to_gradio_audio
from src.config import SUPPORTED_TTS_LANGUAGES
from src.i18n import t

if TYPE_CHECKING:
    from src.error_handler import ErrorHandler
    from src.multi_engine import ModelPool


_EXAMPLE_INSTRUCTS = [
    "一位溫柔、帶有磁性的女聲，語速稍慢",
    "充滿活力的年輕男聲，語調輕快",
    "沉穩的中年男聲，像新聞主播",
    "A warm and friendly female voice with a slight British accent",
    "An energetic young male voice, upbeat and enthusiastic",
]


def _generate(
    text: str,
    instruct: str,
    language: str,
    locale: str,
    model_pool: ModelPool | None,
    error_handler: Any | None,
) -> tuple[Any, str]:
    if not text.strip():
        return None, t("error_empty_text", locale)
    if not instruct.strip():
        return None, "❌ 請輸入音色描述（instruct）"
    if model_pool is None:
        return None, t("error_model_not_loaded", locale)

    try:
        engine = model_pool.get("voice_design")
        result = engine.voice_design(text=text, language=language, instruct=instruct)
        audio_out = to_gradio_audio(result.audio, result.sample_rate)
        status = f"✅ 生成完成  時長 {result.duration:.1f}s  延遲 {result.latency_ms:.0f}ms"
        return audio_out, status
    except Exception as e:
        if error_handler:
            error_handler.add_error("VoiceDesign", str(e))
        return None, f"❌ {e}"


def build_voice_design_tab(
    model_pool: ModelPool | None,
    error_handler: Any | None,
    locale_state: gr.State,
) -> dict[str, Any]:
    """Voice Design 分頁."""
    components: dict[str, Any] = {}

    with gr.Tab("🎨 Voice Design") as tab:
        components["tab_voice_design"] = tab

        gr.Markdown(
            "**描述音色合成** — 用自然語言描述你想要的聲音風格，模型會依描述生成對應音色的語音。\n\n"
            "模型：`Qwen3-TTS-12Hz-0.6B-VoiceDesign`"
        )

        with gr.Row():
            with gr.Column(scale=2):
                text_input = gr.Textbox(
                    label="合成文字",
                    placeholder="輸入要合成的文字內容...",
                    value="歡迎使用聲音設計功能，您可以用文字描述您想要的聲音風格。",
                    lines=5,
                )
                components["vd_text"] = text_input

            with gr.Column(scale=2):
                instruct_input = gr.Textbox(
                    label="音色描述（instruct）",
                    placeholder="描述你想要的聲音，例如：溫柔的女聲，語速稍慢...",
                    value="一位溫柔親切的女聲，語調自然流暢，語速適中。",
                    lines=5,
                )
                components["vd_instruct"] = instruct_input

        with gr.Row():
            language_dd = gr.Dropdown(
                choices=SUPPORTED_TTS_LANGUAGES, value="Chinese",
                label="語言", scale=1,
            )
            components["vd_language"] = language_dd

            gr.Markdown("**範例描述（點擊套用）：**")

        example_btns = []
        with gr.Row():
            for ex in _EXAMPLE_INSTRUCTS[:3]:
                btn = gr.Button(ex[:30] + "…" if len(ex) > 30 else ex, size="sm", scale=1)
                btn.click(fn=lambda e=ex: e, outputs=[instruct_input])
                example_btns.append(btn)

        gen_btn = gr.Button("🎨 生成語音", variant="primary", size="lg")
        components["vd_generate"] = gen_btn

        audio_out = gr.Audio(label="生成音訊", type="numpy")
        components["vd_audio"] = audio_out

        status_out = gr.Textbox(label="狀態", interactive=False, max_lines=2)
        components["vd_status"] = status_out

        gen_btn.click(
            fn=lambda txt, inst, lang, loc: _generate(
                txt, inst, lang, loc, model_pool, error_handler,
            ),
            inputs=[text_input, instruct_input, language_dd, locale_state],
            outputs=[audio_out, status_out],
        )

    return components
