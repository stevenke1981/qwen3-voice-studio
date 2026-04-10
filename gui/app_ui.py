"""Qwen3 Voice Studio — 主 Gradio UI 組裝."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import gradio as gr

from gui.batch_tab import build_batch_tab
from gui.custom_voice_tab import build_custom_voice_tab
from gui.error_panel import build_error_panel
from gui.history_tab import build_history_tab
from gui.monitor_tab import build_monitor_tab
from gui.settings_tab import build_settings_tab
from gui.voice_clone_tab import build_voice_clone_tab
from gui.voice_design_tab import build_voice_design_tab
from gui.workflow_tab import build_workflow_tab
from src.i18n import t

if TYPE_CHECKING:
    from src.error_handler import ErrorHandler
    from src.history import HistoryManager
    from src.multi_engine import ModelPool
    from src.voice_library import VoiceLibrary


_APP_THEME = gr.themes.Soft(
    primary_hue=gr.themes.colors.blue,
    neutral_hue=gr.themes.colors.gray,
).set(
    body_background_fill="*neutral_950",
    body_background_fill_dark="*neutral_950",
    block_background_fill="*neutral_900",
    block_background_fill_dark="*neutral_900",
    input_background_fill="*neutral_800",
    input_background_fill_dark="*neutral_800",
    # 輸入文字強制白色，避免深色背景下看不見
    input_text_size="*text_md",
)

_APP_CSS = """
.gradio-container { max-width: 1280px !important; }
footer { display: none !important; }

/* 輸入框文字顏色 */
textarea,
input[type="text"],
input[type="number"],
input[type="search"],
.block textarea,
.block input {
    color: #e8eaed !important;
    caret-color: #e8eaed !important;
}

/* Dropdown 選項文字 */
.wrap-inner span,
.svelte-select span,
ul.options li {
    color: #e8eaed !important;
}

/* Textbox placeholder */
textarea::placeholder,
input::placeholder {
    color: #9aa0a6 !important;
    opacity: 1 !important;
}

/* 唯讀輸出框同樣需要可見 */
.block .output-class textarea {
    color: #e8eaed !important;
}
"""


def build_app(
    model_pool: ModelPool | None = None,
    voice_lib: VoiceLibrary | None = None,
    history_mgr: HistoryManager | None = None,
    error_handler: ErrorHandler | None = None,
    settings: Any = None,
    default_locale: str = "zh-TW",
) -> gr.Blocks:
    """組裝完整 Gradio App."""
    with gr.Blocks(title="Qwen3 Voice Studio") as app:
        locale_state = gr.State(value=default_locale)

        # ── 頂部列 ──────────────────────────────────────────────────────────
        with gr.Row():
            gr.Markdown("## 🎙️ Qwen3 Voice Studio")
            with gr.Column(scale=0, min_width=200):
                # 模型狀態指示
                if model_pool is not None:
                    loaded = model_pool.loaded_kinds()
                    status_md = "  ".join(
                        f"✅ `{k}`" if k in loaded else f"⬜ `{k}`"
                        for k in ["base", "custom_voice", "voice_design"]
                    )
                    gr.Markdown(f"**模型：** {status_md}", elem_id="model-status")
            locale_dd = gr.Dropdown(
                choices=["zh-TW", "en"],
                value=default_locale,
                label="🌐",
                scale=0,
                min_width=100,
            )

        # ── 分頁 ─────────────────────────────────────────────────────────────
        # Workflow 放在最前面，讓用戶快速上手全流程
        build_workflow_tab(model_pool, error_handler, locale_state)
        build_custom_voice_tab(model_pool, history_mgr, error_handler, locale_state)
        build_voice_design_tab(model_pool, error_handler, locale_state)
        build_voice_clone_tab(model_pool, error_handler, locale_state)
        build_batch_tab(model_pool, error_handler, locale_state)
        build_history_tab(history_mgr, locale_state)
        if settings:
            build_settings_tab(settings, locale_state)
        build_monitor_tab(
            locale_state,
            model_loaded_fn=lambda: bool(model_pool and model_pool.loaded_kinds()),
            last_latency_fn=lambda: 0.0,
        )
        build_error_panel(error_handler, locale_state)

        # ── 語言切換（更新 locale_state） ───────────────────────────────────
        locale_dd.change(
            fn=lambda loc: loc,
            inputs=[locale_dd],
            outputs=[locale_state],
            show_progress="hidden",
        )

    return app
