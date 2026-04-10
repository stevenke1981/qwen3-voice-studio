"""Qwen3 Voice Studio — 歷史紀錄分頁."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import gradio as gr

from src.i18n import t

if TYPE_CHECKING:
    from src.history import HistoryManager


def build_history_tab(
    history_mgr: HistoryManager | None,
    locale_state: gr.State,
) -> dict[str, Any]:
    """建構歷史紀錄分頁."""
    components: dict[str, Any] = {}

    with gr.Tab(t("tab_history", "zh-TW")) as tab:
        components["tab_history"] = tab

        with gr.Row():
            search_input = gr.Textbox(
                label=t("history_search", "zh-TW"),
                placeholder=t("history_search_placeholder", "zh-TW"),
            )
            components["history_search"] = search_input

            search_btn = gr.Button(t("history_search_btn", "zh-TW"))
            components["history_search_btn"] = search_btn

            refresh_btn = gr.Button(t("history_refresh", "zh-TW"))
            components["history_refresh"] = refresh_btn

        history_table = gr.Dataframe(
            headers=[
                t("history_id", "zh-TW"),
                t("history_time", "zh-TW"),
                t("history_text", "zh-TW"),
                t("tts_speaker", "zh-TW"),
                t("tts_language", "zh-TW"),
                t("history_duration", "zh-TW"),
            ],
            label=t("tab_history", "zh-TW"),
            interactive=False,
        )

        clear_btn = gr.Button(t("history_clear", "zh-TW"), variant="stop")
        components["history_clear"] = clear_btn
        status_out = gr.Textbox(label=t("tts_status", "zh-TW"), interactive=False)

        def _refresh() -> list[list[str]]:
            if not history_mgr:
                return []
            return history_mgr.to_table_data()

        def _search(query: str) -> list[list[str]]:
            if not history_mgr:
                return []
            records = history_mgr.search(query)
            return [
                [r.id[:8], r.timestamp, r.text_preview, r.speaker, r.language, f"{r.duration:.1f}s"]
                for r in records
            ]

        def _clear(locale: str) -> tuple[list[list[str]], str]:
            if history_mgr:
                history_mgr.clear()
            return [], t("history_cleared", locale)

        refresh_btn.click(fn=_refresh, outputs=[history_table], show_progress="hidden")
        search_btn.click(fn=_search, inputs=[search_input], outputs=[history_table], show_progress="hidden")
        clear_btn.click(
            fn=_clear, inputs=[locale_state], outputs=[history_table, status_out], show_progress="hidden",
        )
        tab.select(fn=_refresh, outputs=[history_table], show_progress="hidden")

    return components
