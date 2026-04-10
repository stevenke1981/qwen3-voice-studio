"""Qwen3 Voice Studio — 聲音工坊分頁 (聲音庫 / Voice Design / Voice Clone)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import gradio as gr

from src.audio_utils import to_gradio_audio
from src.config import BUILTIN_SPEAKERS, SUPPORTED_TTS_LANGUAGES
from src.i18n import t

if TYPE_CHECKING:
    from src.error_handler import ErrorHandler
    from src.tts_engine import TTSEngine
    from src.voice_library import VoiceLibrary


def _save_voice(
    name: str,
    speaker: str,
    language: str,
    instruct: str,
    pitch: float,
    speed: float,
    energy: float,
    locale: str,
    voice_lib: VoiceLibrary | None,
) -> str:
    if not voice_lib:
        return t("error_voice_lib_unavailable", locale)
    if not name.strip():
        return t("error_empty_name", locale)
    from src.voice_library import VoiceProfile
    profile = VoiceProfile(
        name=name.strip(),
        speaker=speaker,
        language=language,
        instruct=instruct,
        pitch=pitch,
        speed=speed,
        energy=energy,
    )
    voice_lib.save(profile)
    return t("voice_saved", locale).format(name=name)


def _list_voices(voice_lib: VoiceLibrary | None) -> list[list[str]]:
    if not voice_lib:
        return []
    profiles = voice_lib.list_all()
    return [
        [p.name, p.speaker, p.language, p.instruct[:30]]
        for p in profiles
    ]


def _delete_voice(name: str, locale: str, voice_lib: VoiceLibrary | None) -> str:
    if not voice_lib:
        return t("error_voice_lib_unavailable", locale)
    voice_lib.delete(name)
    return t("voice_deleted", locale).format(name=name)


def _voice_design(
    text: str,
    description: str,
    language: str,
    locale: str,
    tts_engine: TTSEngine | None,
    error_handler: ErrorHandler | None,
) -> tuple[Any, str]:
    """Voice Design: 用文字描述創造聲音."""
    if not tts_engine:
        return None, t("error_model_not_loaded", locale)
    if not text.strip() or not description.strip():
        return None, t("error_empty_text", locale)

    try:
        result = tts_engine.voice_design(
            text=text,
            description=description,
            language=language,
        )
        return to_gradio_audio(result.audio, result.sample_rate), t("voice_design_done", locale)
    except Exception as e:
        if error_handler:
            error_handler.add_error("VoiceDesign", str(e))
        return None, f"❌ {e}"


def _voice_clone(
    text: str,
    ref_audio: Any,
    language: str,
    locale: str,
    tts_engine: TTSEngine | None,
    error_handler: ErrorHandler | None,
) -> tuple[Any, str]:
    """Voice Clone: 用參考音檔複製聲音."""
    if not tts_engine:
        return None, t("error_model_not_loaded", locale)
    if not text.strip():
        return None, t("error_empty_text", locale)
    if ref_audio is None:
        return None, t("error_no_ref_audio", locale)

    try:
        if isinstance(ref_audio, tuple):
            sr, audio_data = ref_audio
        else:
            return None, t("error_invalid_audio", locale)

        result = tts_engine.voice_clone(
            text=text,
            ref_audio=audio_data,
            ref_sr=sr,
            language=language,
        )
        return to_gradio_audio(result.audio, result.sample_rate), t("voice_clone_done", locale)
    except Exception as e:
        if error_handler:
            error_handler.add_error("VoiceClone", str(e))
        return None, f"❌ {e}"


def build_voice_tab(
    tts_engine: TTSEngine | None,
    voice_lib: VoiceLibrary | None,
    error_handler: ErrorHandler | None,
    locale_state: gr.State,
) -> dict[str, Any]:
    """建構聲音工坊分頁."""
    components: dict[str, Any] = {}

    with gr.Tab(t("tab_voice", "zh-TW")) as tab:
        components["tab_voice"] = tab

        # ── 聲音庫子分頁 ──
        with gr.Tab(t("voice_library", "zh-TW")) as lib_tab:
            components["voice_library"] = lib_tab

            with gr.Row():
                with gr.Column(scale=1):
                    name_input = gr.Textbox(label=t("voice_name", "zh-TW"))
                    components["voice_name"] = name_input

                    spk_dd = gr.Dropdown(
                        choices=BUILTIN_SPEAKERS,
                        value="Vivian",
                        label=t("tts_speaker", "zh-TW"),
                    )
                    lang_dd = gr.Dropdown(
                        choices=SUPPORTED_TTS_LANGUAGES,
                        value="Chinese",
                        label=t("tts_language", "zh-TW"),
                    )
                    instruct_in = gr.Textbox(
                        label=t("tts_instruct", "zh-TW"), lines=2,
                    )
                    pitch_sl = gr.Slider(0.5, 2.0, value=1.0, step=0.1, label=t("voice_pitch", "zh-TW"))
                    components["voice_pitch"] = pitch_sl
                    speed_sl = gr.Slider(0.5, 2.0, value=1.0, step=0.1, label=t("voice_speed", "zh-TW"))
                    components["voice_speed"] = speed_sl
                    energy_sl = gr.Slider(0.5, 2.0, value=1.0, step=0.1, label=t("voice_energy", "zh-TW"))
                    components["voice_energy"] = energy_sl

                    save_btn = gr.Button(t("voice_save", "zh-TW"), variant="primary")
                    components["voice_save"] = save_btn
                    lib_status = gr.Textbox(label=t("tts_status", "zh-TW"), interactive=False)

                with gr.Column(scale=2):
                    voice_table = gr.Dataframe(
                        headers=[
                            t("voice_name", "zh-TW"),
                            t("tts_speaker", "zh-TW"),
                            t("tts_language", "zh-TW"),
                            t("tts_instruct", "zh-TW"),
                        ],
                        label=t("voice_library", "zh-TW"),
                        interactive=False,
                    )
                    refresh_btn = gr.Button(t("voice_refresh", "zh-TW"))
                    components["voice_refresh"] = refresh_btn

                    del_name = gr.Textbox(label=t("voice_delete_name", "zh-TW"))
                    del_btn = gr.Button(t("voice_delete", "zh-TW"), variant="stop")
                    components["voice_delete"] = del_btn

            save_btn.click(
                fn=lambda n, s, la, i, p, sp, e, loc: _save_voice(
                    n, s, la, i, p, sp, e, loc, voice_lib,
                ),
                inputs=[name_input, spk_dd, lang_dd, instruct_in, pitch_sl, speed_sl, energy_sl, locale_state],
                outputs=[lib_status],
            )
            refresh_btn.click(
                fn=lambda: _list_voices(voice_lib),
                outputs=[voice_table],
            )
            del_btn.click(
                fn=lambda n, loc: _delete_voice(n, loc, voice_lib),
                inputs=[del_name, locale_state],
                outputs=[lib_status],
            )

        # ── Voice Design 子分頁 ──
        with gr.Tab(t("voice_design", "zh-TW")) as design_tab:
            components["voice_design"] = design_tab

            gr.Markdown(t("voice_design_desc", "zh-TW"))
            vd_text = gr.Textbox(label=t("tts_input_text", "zh-TW"), lines=3)
            vd_desc = gr.Textbox(
                label=t("voice_design_description", "zh-TW"),
                placeholder=t("voice_design_placeholder", "zh-TW"),
                lines=2,
            )
            components["voice_design_description"] = vd_desc
            vd_lang = gr.Dropdown(
                choices=SUPPORTED_TTS_LANGUAGES,
                value="Chinese",
                label=t("tts_language", "zh-TW"),
            )
            vd_btn = gr.Button(t("voice_design_generate", "zh-TW"), variant="primary")
            components["voice_design_generate"] = vd_btn
            vd_audio = gr.Audio(label=t("tts_audio_output", "zh-TW"), type="numpy")
            vd_status = gr.Textbox(label=t("tts_status", "zh-TW"), interactive=False)

            vd_btn.click(
                fn=lambda txt, desc, lang, loc: _voice_design(
                    txt, desc, lang, loc, tts_engine, error_handler,
                ),
                inputs=[vd_text, vd_desc, vd_lang, locale_state],
                outputs=[vd_audio, vd_status],
            )

        # ── Voice Clone 子分頁 ──
        with gr.Tab(t("voice_clone", "zh-TW")) as clone_tab:
            components["voice_clone"] = clone_tab

            gr.Markdown(t("voice_clone_desc", "zh-TW"))
            vc_text = gr.Textbox(label=t("tts_input_text", "zh-TW"), lines=3)
            vc_ref = gr.Audio(
                label=t("voice_clone_ref", "zh-TW"),
                type="numpy",
            )
            components["voice_clone_ref"] = vc_ref
            vc_lang = gr.Dropdown(
                choices=SUPPORTED_TTS_LANGUAGES,
                value="Chinese",
                label=t("tts_language", "zh-TW"),
            )
            vc_btn = gr.Button(t("voice_clone_generate", "zh-TW"), variant="primary")
            components["voice_clone_generate"] = vc_btn
            vc_audio = gr.Audio(label=t("tts_audio_output", "zh-TW"), type="numpy")
            vc_status = gr.Textbox(label=t("tts_status", "zh-TW"), interactive=False)

            vc_btn.click(
                fn=lambda txt, ref, lang, loc: _voice_clone(
                    txt, ref, lang, loc, tts_engine, error_handler,
                ),
                inputs=[vc_text, vc_ref, vc_lang, locale_state],
                outputs=[vc_audio, vc_status],
            )

    return components
