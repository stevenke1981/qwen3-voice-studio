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
from gui.youtube_tab import build_youtube_tab
from src.i18n import t

if TYPE_CHECKING:
    from src.error_handler import ErrorHandler
    from src.history import HistoryManager
    from src.multi_engine import ModelPool
    from src.voice_library import VoiceLibrary


# ── 主題：深色 + 藍色強調 ─────────────────────────────────────────────────────
_APP_THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.blue,
    secondary_hue=gr.themes.colors.sky,
    neutral_hue=gr.themes.colors.slate,
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "monospace"],
).set(
    # 背景
    body_background_fill="#0f1117",
    body_background_fill_dark="#0f1117",
    # Block 卡片
    block_background_fill="#1a1d27",
    block_background_fill_dark="#1a1d27",
    block_border_color="#2d3045",
    block_border_color_dark="#2d3045",
    block_border_width="1px",
    block_radius="12px",
    block_shadow="0 4px 24px rgba(0,0,0,0.4)",
    # 輸入框
    input_background_fill="#0f1117",
    input_background_fill_dark="#0f1117",
    input_border_color="#3a3d52",
    input_border_color_dark="#3a3d52",
    input_border_width="1px",
    input_radius="8px",
    # 按鈕
    button_primary_background_fill="#3b6ff0",
    button_primary_background_fill_hover="#2d5ce8",
    button_primary_border_color="#3b6ff0",
    button_primary_text_color="#ffffff",
    button_secondary_background_fill="#2a2d3e",
    button_secondary_background_fill_hover="#343750",
    button_secondary_border_color="#3a3d52",
    button_secondary_text_color="#c8cde8",
    button_large_radius="8px",
    button_small_radius="6px",
    # 文字
    body_text_color="#c8cde8",
    body_text_color_dark="#c8cde8",
    body_text_size="15px",
    block_label_text_color="#8b92b8",
    block_label_text_size="13px",
    block_title_text_color="#e2e6ff",
    block_title_text_size="15px",
    block_title_text_weight="600",
)


_APP_CSS = """
/* ═══════════════════════════════════════════════════════
   Qwen3 Voice Studio — Global Styles
   ═══════════════════════════════════════════════════════ */

:root {
  --bg-base:    #0f1117;
  --bg-card:    #1a1d27;
  --bg-input:   #0f1117;
  --border:     #2d3045;
  --border-hi:  #3b6ff0;
  --text-pri:   #e2e6ff;
  --text-sec:   #c8cde8;
  --text-muted: #8b92b8;
  --accent:     #3b6ff0;
  --accent-glow:rgba(59,111,240,0.25);
  --green:      #22c55e;
  --yellow:     #f59e0b;
  --red:        #ef4444;
}

/* ── 容器 ── */
.gradio-container {
  max-width: 1340px !important;
  margin: 0 auto !important;
  padding: 0 16px !important;
}
footer { display: none !important; }

/* ── 全域文字 ── */
*, *::before, *::after { box-sizing: border-box; }

body, .gradio-container, .wrap, .block, .form,
label, span, p, div, h1, h2, h3, h4, button {
  color: var(--text-sec);
}

/* ── Markdown ── */
.prose, .md, .markdown {
  color: var(--text-sec) !important;
}
.prose strong, .md strong { color: var(--text-pri) !important; }
.prose code, .md code {
  background: rgba(59,111,240,0.15) !important;
  color: #7aa3ff !important;
  padding: 1px 6px;
  border-radius: 4px;
}

/* ── Block label / title ── */
.block .label-wrap span,
.block > label > span,
span.svelte-1gfkn6j,
.form label span,
label span {
  color: var(--text-muted) !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  letter-spacing: 0.03em !important;
  text-transform: uppercase !important;
}

/* ── 輸入框 ── */
textarea,
input[type="text"],
input[type="number"],
input[type="search"],
input[type="url"],
.block textarea,
.block input {
  background: var(--bg-input) !important;
  color: var(--text-pri) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  padding: 10px 14px !important;
  font-size: 14px !important;
  transition: border-color .2s;
}
textarea:focus,
input:focus {
  border-color: var(--border-hi) !important;
  box-shadow: 0 0 0 3px var(--accent-glow) !important;
  outline: none !important;
}
textarea::placeholder, input::placeholder {
  color: #4a5280 !important;
}

/* ── Dropdown ── */
.wrap-inner, .wrap-inner span,
ul.options li, .options li span,
[data-testid="dropdown"] span,
.svelte-select span {
  color: var(--text-sec) !important;
}
.options { background: var(--bg-card) !important; border: 1px solid var(--border) !important; }
.options li:hover { background: rgba(59,111,240,.2) !important; }
.options li.selected { background: rgba(59,111,240,.35) !important; color: #fff !important; }

/* ── Tabs ── */
.tab-nav { border-bottom: 1px solid var(--border) !important; }
button[role="tab"] {
  color: var(--text-muted) !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  padding: 10px 18px !important;
  border-radius: 8px 8px 0 0 !important;
  transition: color .2s, background .2s;
}
button[role="tab"]:hover { color: var(--text-sec) !important; background: rgba(255,255,255,.04) !important; }
button[role="tab"][aria-selected="true"] {
  color: #ffffff !important;
  font-weight: 700 !important;
  border-bottom: 2px solid var(--accent) !important;
  background: rgba(59,111,240,.1) !important;
}

/* ── Accordion ── */
.accordion {
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  margin-bottom: 8px !important;
}
.accordion-header button {
  color: var(--text-pri) !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  padding: 14px 16px !important;
}
.accordion-header button:hover { background: rgba(255,255,255,.04) !important; }

/* ── Buttons ── */
button.primary {
  background: linear-gradient(135deg, #3b6ff0, #2d5ce8) !important;
  color: #fff !important;
  font-weight: 600 !important;
  font-size: 15px !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(59,111,240,.4) !important;
  transition: transform .1s, box-shadow .2s !important;
}
button.primary:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 20px rgba(59,111,240,.55) !important;
}
button.primary:active { transform: translateY(0) !important; }
button.secondary {
  background: rgba(255,255,255,.07) !important;
  color: var(--text-sec) !important;
  border: 1px solid var(--border) !important;
  font-weight: 500 !important;
}
button.secondary:hover { background: rgba(255,255,255,.12) !important; }

/* ── Sliders ── */
input[type="range"] { accent-color: var(--accent) !important; }
.range-slider span, .svelte-slider span { color: var(--text-sec) !important; }

/* ── Checkbox & Radio ── */
.checkbox-label span, .radio-label span,
input[type="checkbox"] + span, input[type="radio"] + span {
  color: var(--text-sec) !important;
}
input[type="checkbox"] { accent-color: var(--accent) !important; }

/* ── File Upload ── */
.file-component, .upload-container {
  border: 2px dashed var(--border) !important;
  border-radius: 10px !important;
  background: rgba(59,111,240,.04) !important;
  transition: border-color .2s;
}
.file-component:hover { border-color: var(--accent) !important; }

/* ── Audio Component ── */
.audio-component, [data-testid="audio"] {
  border-radius: 10px !important;
  overflow: hidden;
}

/* ── Status badges (custom) ── */
.status-ok   { color: var(--green)  !important; font-weight: 600; }
.status-warn { color: var(--yellow) !important; font-weight: 600; }
.status-err  { color: var(--red)    !important; font-weight: 600; }

/* ── Header bar ── */
#app-header {
  background: linear-gradient(90deg, rgba(59,111,240,.15), transparent);
  border-bottom: 1px solid var(--border);
  padding: 16px 24px;
  border-radius: 12px 12px 0 0;
  margin-bottom: 4px;
}
#app-header .title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-pri);
  letter-spacing: -0.02em;
}
#app-header .subtitle {
  font-size: 13px;
  color: var(--text-muted);
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
    with gr.Blocks(title="Qwen3 Voice Studio", theme=_APP_THEME, css=_APP_CSS) as app:
        locale_state = gr.State(value=default_locale)

        # ── Header ──────────────────────────────────────────────────────────
        with gr.Row(elem_id="app-header"):
            with gr.Column(scale=4):
                gr.HTML("""
                <div class="title">🎙️ Qwen3 Voice Studio</div>
                <div class="subtitle">多模型語音工作站 · CustomVoice · VoiceDesign · VoiceClone · Workflow</div>
                """)
            with gr.Column(scale=1, min_width=200):
                if model_pool is not None:
                    loaded = model_pool.loaded_kinds()
                    badges = "".join(
                        f'<span class="status-ok">✓ {k}</span>&nbsp;&nbsp;'
                        if k in loaded else
                        f'<span class="status-warn">○ {k}</span>&nbsp;&nbsp;'
                        for k in ["base", "custom_voice", "voice_design"]
                    )
                    gr.HTML(f'<div style="font-size:12px;line-height:2">{badges}</div>')
            with gr.Column(scale=0, min_width=120):
                locale_dd = gr.Dropdown(
                    choices=["zh-TW", "en"],
                    value=default_locale,
                    label="🌐 語言",
                    container=False,
                )

        # ── Tabs ─────────────────────────────────────────────────────────────
        build_workflow_tab(model_pool, error_handler, locale_state)
        build_custom_voice_tab(model_pool, history_mgr, error_handler, locale_state)
        build_voice_design_tab(model_pool, error_handler, locale_state)
        build_voice_clone_tab(model_pool, error_handler, locale_state)
        build_youtube_tab()
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

        locale_dd.change(
            fn=lambda loc: loc,
            inputs=[locale_dd],
            outputs=[locale_state],
            show_progress="hidden",
        )

    return app
