"""Qwen3 Voice Studio — 效能監控分頁."""

from __future__ import annotations

from typing import Any

import gradio as gr

from src.i18n import t
from src.monitor import format_metrics_display, get_system_metrics


def build_monitor_tab(
    locale_state: gr.State,
    model_loaded_fn: Any = None,
    last_latency_fn: Any = None,
) -> dict[str, Any]:
    """建構效能監控分頁."""
    components: dict[str, Any] = {}

    with gr.Tab(t("tab_monitor", "zh-TW")) as tab:
        components["tab_monitor"] = tab

        monitor_output = gr.Textbox(
            label=t("monitor_title", "zh-TW"),
            lines=10,
            interactive=False,
        )
        components["monitor_title"] = monitor_output

        refresh_btn = gr.Button(t("monitor_refresh", "zh-TW"))
        components["monitor_refresh"] = refresh_btn

        def _refresh(locale: str) -> str:
            loaded = model_loaded_fn() if model_loaded_fn else False
            latency = last_latency_fn() if last_latency_fn else 0.0
            metrics = get_system_metrics(model_loaded=loaded, last_latency=latency)
            return format_metrics_display(metrics, locale)

        refresh_btn.click(fn=_refresh, inputs=[locale_state], outputs=[monitor_output], show_progress="hidden")
        tab.select(fn=_refresh, inputs=[locale_state], outputs=[monitor_output], show_progress="hidden")

    return components
