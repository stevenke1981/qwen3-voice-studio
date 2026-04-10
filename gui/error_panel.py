"""Qwen3 Voice Studio — 錯誤日誌面板."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import gradio as gr

from src.i18n import t

if TYPE_CHECKING:
    from src.error_handler import ErrorHandler


def build_error_panel(
    error_handler: ErrorHandler | None,
    locale_state: gr.State,
) -> dict[str, Any]:
    """建構錯誤日誌面板."""
    components: dict[str, Any] = {}

    with gr.Tab(t("tab_errors", "zh-TW")) as tab:
        components["tab_errors"] = tab

        error_output = gr.Textbox(
            label=t("error_log_title", "zh-TW"),
            lines=15,
            interactive=False,
        )
        components["error_log_title"] = error_output

        with gr.Row():
            refresh_btn = gr.Button(t("error_refresh", "zh-TW"))
            components["error_refresh"] = refresh_btn

            export_btn = gr.Button(t("error_export", "zh-TW"))
            components["error_export"] = export_btn

            clear_btn = gr.Button(t("error_clear", "zh-TW"), variant="stop")
            components["error_clear"] = clear_btn

        export_status = gr.Textbox(label=t("tts_status", "zh-TW"), interactive=False)

        def _refresh() -> str:
            if not error_handler:
                return ""
            return error_handler.format_for_display()

        def _export(locale: str) -> str:
            if not error_handler:
                return ""
            path = error_handler.export_csv()
            return t("error_exported", locale).format(path=path)

        def _clear() -> str:
            if error_handler:
                error_handler.clear()
            return ""

        refresh_btn.click(fn=_refresh, outputs=[error_output])
        export_btn.click(fn=_export, inputs=[locale_state], outputs=[export_status])
        clear_btn.click(fn=_clear, outputs=[error_output])
        tab.select(fn=_refresh, outputs=[error_output])

    return components
