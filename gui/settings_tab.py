"""Qwen3 Voice Studio — 設定分頁."""

from __future__ import annotations

from typing import Any

import gradio as gr

from src.config import ALL_MODEL_IDS, AppSettings
from src.i18n import t


def build_settings_tab(
    settings: AppSettings,
    locale_state: gr.State,
) -> dict[str, Any]:
    """建構設定分頁."""
    components: dict[str, Any] = {}

    with gr.Tab(t("tab_settings", "zh-TW")) as tab:
        components["tab_settings"] = tab

        gr.Markdown(f"### {t('settings_title', 'zh-TW')}")

        with gr.Group():
            gr.Markdown("#### 模型路徑設定")

            cv_model = gr.Dropdown(
                choices=ALL_MODEL_IDS,
                value=settings.tts.custom_voice_model,
                allow_custom_value=True,
                label="CustomVoice 模型（具名音色）",
                interactive=True,
            )
            vd_model = gr.Dropdown(
                choices=ALL_MODEL_IDS,
                value=settings.tts.voice_design_model,
                allow_custom_value=True,
                label="VoiceDesign 模型（描述音色）",
                interactive=True,
            )
            base_model = gr.Dropdown(
                choices=ALL_MODEL_IDS,
                value=settings.tts.base_model,
                allow_custom_value=True,
                label="Base 模型（聲音克隆）",
                interactive=True,
            )

            device_input = gr.Textbox(
                label=t("settings_device", "zh-TW"),
                value=settings.tts.device,
                interactive=True,
            )
            components["settings_device"] = device_input

        with gr.Group():
            gr.Markdown("#### SRT 字幕設定")

            srt_mode_radio = gr.Radio(
                choices=["uniform", "rate"],
                value=settings.tts.srt_mode,
                label=t("settings_srt_mode", "zh-TW"),
            )
            components["settings_srt_mode"] = srt_mode_radio

            zh_cpm_slider = gr.Slider(
                minimum=60, maximum=600, value=settings.tts.zh_cpm, step=10,
                label=t("settings_zh_cpm", "zh-TW"),
            )
            components["settings_zh_cpm"] = zh_cpm_slider

            en_wpm_slider = gr.Slider(
                minimum=60, maximum=400, value=settings.tts.en_wpm, step=10,
                label=t("settings_en_wpm", "zh-TW"),
            )
            components["settings_en_wpm"] = en_wpm_slider

        with gr.Group():
            gr.Markdown("#### 輸出設定")

            output_dir_input = gr.Textbox(
                label=t("settings_output_dir", "zh-TW"),
                value=settings.tts.output_dir,
                placeholder="留空使用預設目錄",
                interactive=True,
            )
            components["settings_output_dir"] = output_dir_input

            auto_start_cb = gr.Checkbox(
                label=t("settings_auto_start", "zh-TW"),
                value=settings.tts.auto_start,
            )
            components["settings_auto_start"] = auto_start_cb

        save_btn = gr.Button(t("settings_save", "zh-TW"), variant="primary")
        components["settings_save"] = save_btn

        status_out = gr.Textbox(label=t("tts_status", "zh-TW"), interactive=False)

        def _save(
            cv: str, vd: str, base: str,
            device: str,
            srt_m: str, zh: float, en: float,
            out_dir: str, auto: bool,
            locale: str,
        ) -> str:
            updated = AppSettings(
                locale=locale,
                tts=settings.tts.model_copy(
                    update={
                        "custom_voice_model": cv,
                        "voice_design_model": vd,
                        "base_model": base,
                        "device": device,
                        "srt_mode": srt_m,
                        "zh_cpm": int(zh),
                        "en_wpm": int(en),
                        "output_dir": out_dir,
                        "auto_start": auto,
                    },
                ),
            )
            updated.save()
            return t("settings_saved", locale)

        save_btn.click(
            fn=_save,
            inputs=[
                cv_model, vd_model, base_model,
                device_input,
                srt_mode_radio, zh_cpm_slider, en_wpm_slider,
                output_dir_input, auto_start_cb, locale_state,
            ],
            outputs=[status_out],
        )

    return components
