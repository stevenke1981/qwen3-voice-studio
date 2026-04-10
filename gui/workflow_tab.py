"""Qwen3 Voice Studio — Workflow 串聯分頁.

將三種模型組合成完整的語音生產工作流：

  Step 1  Voice Design  → 用描述生成語音樣本（作為聲音設計原型）
  Step 2  Voice Clone   → 以 Step 1 的音訊為參考，克隆音色到新文字
  Step 3  Batch Export  → 將最終音色批量套用到多段文字並匯出

設計理念：
  - 每個 Step 的輸出可直接傳入下一個 Step
  - 任何 Step 也可獨立使用（直接上傳或手動填入）
"""

from __future__ import annotations

import io
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

import gradio as gr
import numpy as np

from src.audio_utils import to_gradio_audio
from src.config import SUPPORTED_TTS_LANGUAGES
from utils.srt_generator import generate_srt

if TYPE_CHECKING:
    from src.error_handler import ErrorHandler
    from src.multi_engine import ModelPool


def _step1_design(
    design_text: str,
    design_instruct: str,
    language: str,
    model_pool: ModelPool | None,
    error_handler: Any | None,
) -> tuple[Any, Any, str]:
    """Step 1: Voice Design → 生成聲音原型."""
    if not design_text.strip() or not design_instruct.strip():
        return None, None, "❌ 請填入合成文字與音色描述"
    if model_pool is None:
        return None, None, "❌ 模型未載入"
    try:
        engine = model_pool.get("voice_design")
        result = engine.voice_design(text=design_text, language=language, instruct=design_instruct)
        audio_out = to_gradio_audio(result.audio, result.sample_rate)

        # 儲存為暫存 WAV 供 Step 2 使用
        import soundfile as sf
        buf = io.BytesIO()
        sf.write(buf, result.audio, result.sample_rate, format="WAV")
        buf.seek(0)
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.write(buf.read())
        tmp.flush()

        status = f"✅ Step 1 完成  時長 {result.duration:.1f}s  → 音頻已傳入 Step 2"
        return audio_out, tmp.name, status
    except Exception as e:
        if error_handler:
            error_handler.add_error("Workflow-Step1", str(e))
        return None, None, f"❌ {e}"


def _step2_clone(
    clone_text: str,
    ref_audio_path: str | None,
    ref_audio_upload: Any,
    language: str,
    model_pool: ModelPool | None,
    error_handler: Any | None,
) -> tuple[Any, Any, str]:
    """Step 2: Voice Clone → 用 Step 1 音色克隆新文字."""
    if not clone_text.strip():
        return None, None, "❌ 請填入合成文字"

    # 優先用 Step 1 傳來的路徑，否則用手動上傳
    ref_path = ref_audio_path or (
        ref_audio_upload.name if ref_audio_upload and hasattr(ref_audio_upload, "name") else None
    )
    if not ref_path:
        return None, None, "❌ 請先執行 Step 1 或手動上傳參考音頻"

    if model_pool is None:
        return None, None, "❌ 模型未載入"

    try:
        import soundfile as sf
        data, sr = sf.read(ref_path, dtype="float32")
        if data.ndim > 1:
            data = data.mean(axis=1)

        engine = model_pool.get("base")
        result = engine.voice_clone(
            text=clone_text, language=language,
            ref_audio=(data, sr), x_vector_only=True,
        )
        audio_out = to_gradio_audio(result.audio, result.sample_rate)

        # 儲存供 Step 3 使用
        buf = io.BytesIO()
        sf.write(buf, result.audio, result.sample_rate, format="WAV")
        buf.seek(0)
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.write(buf.read())
        tmp.flush()

        status = f"✅ Step 2 完成  時長 {result.duration:.1f}s  → 音色已鎖定，可進入 Step 3 批量匯出"
        return audio_out, tmp.name, status
    except Exception as e:
        if error_handler:
            error_handler.add_error("Workflow-Step2", str(e))
        return None, None, f"❌ {e}"


def _step3_batch(
    batch_texts: str,
    cloned_ref_path: str | None,
    language: str,
    srt_mode: str,
    model_pool: ModelPool | None,
    error_handler: Any | None,
) -> tuple[list[str] | None, str]:
    """Step 3: 批量套用克隆音色匯出多段音頻."""
    lines = [l.strip() for l in batch_texts.strip().splitlines() if l.strip()]
    if not lines:
        return None, "❌ 請在文字框中輸入要合成的段落（每行一段）"
    if not cloned_ref_path:
        return None, "❌ 請先完成 Step 2 克隆音色"
    if model_pool is None:
        return None, "❌ 模型未載入"

    try:
        import soundfile as sf
        ref_data, ref_sr = sf.read(cloned_ref_path, dtype="float32")
        if ref_data.ndim > 1:
            ref_data = ref_data.mean(axis=1)

        engine = model_pool.get("base")
        output_dir = Path(tempfile.mkdtemp(prefix="qwen3_workflow_"))
        output_files = []

        for i, line in enumerate(lines, 1):
            result = engine.voice_clone(
                text=line, language=language,
                ref_audio=(ref_data, ref_sr), x_vector_only=True,
            )
            wav_path = output_dir / f"{i:04d}.wav"
            import soundfile as sf
            sf.write(str(wav_path), result.audio, result.sample_rate)
            output_files.append(str(wav_path))

            if srt_mode != "none":
                srt = generate_srt(text=line, total_duration=result.duration, mode=srt_mode)
                (output_dir / f"{i:04d}.srt").write_text(srt, encoding="utf-8")

        status = f"✅ Step 3 完成  {len(lines)} 段  輸出目錄：{output_dir}"
        return output_files, status
    except Exception as e:
        if error_handler:
            error_handler.add_error("Workflow-Step3", str(e))
        return None, f"❌ {e}"


def build_workflow_tab(
    model_pool: ModelPool | None,
    error_handler: Any | None,
    locale_state: gr.State,
) -> dict[str, Any]:
    """Workflow 串聯分頁."""
    components: dict[str, Any] = {}

    with gr.Tab("⚡ Workflow") as tab:
        components["tab_workflow"] = tab

        gr.Markdown(
            "## 三步驟語音生產工作流\n\n"
            "**Step 1** `VoiceDesign` → 描述音色原型  \n"
            "**Step 2** `VoiceClone` → 以原型克隆到新文字  \n"
            "**Step 3** `Batch` → 批量套用克隆音色匯出\n\n"
            "每個步驟可獨立執行，也可串聯自動傳遞結果。"
        )

        language_dd = gr.Dropdown(
            choices=["Chinese", "English", "Japanese"], value="Chinese",
            label="語言（全流程共用）", scale=0, min_width=150,
        )

        # ── Step 1 ──────────────────────────────────────────────────────────
        with gr.Accordion("Step 1：聲音設計 (VoiceDesign)", open=True):
            with gr.Row():
                s1_text = gr.Textbox(
                    label="設計用合成文字（用於試聽音色）",
                    placeholder="例：這是一段測試語音。",
                    value="這是聲音設計的試聽範例，請聆聽音色效果。",
                    lines=3, scale=2,
                )
                s1_instruct = gr.Textbox(
                    label="音色描述",
                    placeholder="例：溫柔的女聲，帶有輕微磁性，語速稍慢",
                    value="溫柔親切的女聲，語調自然，語速適中，帶有輕微磁性。",
                    lines=3, scale=2,
                )
            s1_btn = gr.Button("▶ 執行 Step 1", variant="primary")
            s1_audio = gr.Audio(label="Step 1 輸出音頻", type="numpy")
            s1_ref_path = gr.State(value=None)  # 傳給 Step 2 的暫存路徑
            s1_status = gr.Textbox(label="Step 1 狀態", interactive=False, max_lines=2)

        # ── Step 2 ──────────────────────────────────────────────────────────
        with gr.Accordion("Step 2：聲音克隆 (VoiceClone)", open=True):
            gr.Markdown("_自動使用 Step 1 的音頻；也可手動上傳參考音頻覆蓋。_")
            with gr.Row():
                s2_text = gr.Textbox(
                    label="克隆目標文字",
                    placeholder="輸入要用克隆音色合成的文字...",
                    value="以上是聲音設計的效果，現在我們用同樣的音色來合成這段新文字。",
                    lines=4, scale=3,
                )
                s2_ref_upload = gr.File(
                    label="手動參考音頻（覆蓋 Step 1）",
                    file_types=[".wav", ".mp3"], scale=1,
                )
            s2_btn = gr.Button("▶ 執行 Step 2", variant="primary")
            s2_audio = gr.Audio(label="Step 2 克隆音頻", type="numpy")
            s2_ref_path = gr.State(value=None)  # 傳給 Step 3
            s2_status = gr.Textbox(label="Step 2 狀態", interactive=False, max_lines=2)

        # ── Step 3 ──────────────────────────────────────────────────────────
        with gr.Accordion("Step 3：批量匯出 (Batch)", open=False):
            gr.Markdown("_每行一段文字，全部以 Step 2 克隆的音色合成並匯出。_")
            s3_texts = gr.Textbox(
                label="批量文字（每行一段）",
                placeholder="第一段文字\n第二段文字\n第三段文字...",
                value="第一章：故事的開始，一切都從這裡展開。\n第二章：主角踏上了未知的旅程。\n第三章：困難與挑戰接踵而來。",
                lines=8,
            )
            srt_dd = gr.Dropdown(
                choices=["none", "uniform", "rate"], value="uniform",
                label="SRT 模式",
            )
            s3_btn = gr.Button("▶ 執行 Step 3 批量匯出", variant="primary")
            s3_files = gr.File(label="匯出檔案", visible=True)
            s3_status = gr.Textbox(label="Step 3 狀態", interactive=False, max_lines=3)

        # ── 事件綁定 ────────────────────────────────────────────────────────
        s1_btn.click(
            fn=lambda txt, inst, lang: _step1_design(txt, inst, lang, model_pool, error_handler),
            inputs=[s1_text, s1_instruct, language_dd],
            outputs=[s1_audio, s1_ref_path, s1_status],
        )

        s2_btn.click(
            fn=lambda txt, ref_p, ref_u, lang: _step2_clone(
                txt, ref_p, ref_u, lang, model_pool, error_handler,
            ),
            inputs=[s2_text, s1_ref_path, s2_ref_upload, language_dd],
            outputs=[s2_audio, s2_ref_path, s2_status],
        )

        s3_btn.click(
            fn=lambda txts, ref_p, lang, srt_m: _step3_batch(
                txts, ref_p, lang, srt_m, model_pool, error_handler,
            ),
            inputs=[s3_texts, s2_ref_path, language_dd, srt_dd],
            outputs=[s3_files, s3_status],
        )

    return components
