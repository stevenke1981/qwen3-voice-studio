"""Qwen3 Voice Studio — YouTube / 影片音訊提取分頁.

功能：
  1. 輸入 URL（YouTube / BiliBili / Twitter 等 yt-dlp 支援的網站）
  2. 下載影片並提取音訊（WAV 24kHz mono）
  3. 播放完整音訊、查看時長
  4. 以滑桿選取起始/結束時間區段
  5. 預覽所選區段
  6. 儲存區段為 WAV 到 wav-template/ 目錄，供 VoiceClone 使用
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import gradio as gr
import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)

WAV_TEMPLATE_DIR = Path("wav-template")


def _ensure_template_dir() -> Path:
    WAV_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    return WAV_TEMPLATE_DIR


def _sanitize_filename(name: str) -> str:
    """清理非法字元，用於檔名。"""
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name[:80] or "audio"


def _download_audio(url: str) -> tuple[str | None, str]:
    """用 yt-dlp 下載音訊，回傳 (wav_path, status_msg)。"""
    url = url.strip()
    if not url:
        return None, "❌ 請輸入 URL"

    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        return None, "❌ 缺少 yt-dlp，請執行：uv pip install yt-dlp"

    tmp_dir = Path(tempfile.mkdtemp(prefix="qwen3_yt_"))
    out_template = str(tmp_dir / "%(title)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
        }],
    }

    try:
        import yt_dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "audio") if info else "audio"

        # 找到下載的 wav 檔
        wav_files = list(tmp_dir.glob("*.wav"))
        if not wav_files:
            return None, "❌ 下載失敗：找不到輸出的 WAV 檔案"

        wav_path = str(wav_files[0])

        # 轉換為 24kHz mono（標準格式）
        out_path = str(tmp_dir / f"{_sanitize_filename(title)}_24k.wav")
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", wav_path,
             "-ac", "1", "-ar", "24000", "-sample_fmt", "s16", out_path],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            return wav_path, f"⚠️ 格式轉換失敗（使用原始格式）：{result.stderr[-200:]}"

        data, sr = sf.read(out_path, dtype="float32")
        duration = len(data) / sr
        return out_path, f"✅ 下載完成｜**{title}**｜時長 {duration:.1f}s｜{sr}Hz mono"

    except Exception as e:
        logger.error("yt-dlp 下載失敗: %s", e)
        return None, f"❌ 下載失敗：{e}"


def _read_audio(wav_path: str | None) -> tuple[tuple[int, np.ndarray] | None, float, str]:
    """讀取 WAV，回傳 (gradio_audio, duration_seconds, info)。"""
    if not wav_path or not Path(wav_path).exists():
        return None, 0.0, ""
    try:
        data, sr = sf.read(wav_path, dtype="float32")
        if data.ndim > 1:
            data = data.mean(axis=1)
        duration = len(data) / sr
        # int16 for gradio
        max_v = np.abs(data).max()
        if max_v > 0:
            data = data / max_v
        audio_i16 = np.clip(data * 32767, -32768, 32767).astype(np.int16)
        info = f"時長：{duration:.2f}s  |  採樣率：{sr}Hz  |  {len(data)} samples"
        return (sr, audio_i16), duration, info
    except Exception as e:
        return None, 0.0, f"讀取失敗：{e}"


def _crop_and_preview(
    wav_path: str | None,
    start_sec: float,
    end_sec: float,
) -> tuple[tuple[int, np.ndarray] | None, str]:
    """裁剪選取區段並回傳預覽音訊。"""
    if not wav_path:
        return None, "❌ 請先下載音訊"
    try:
        data, sr = sf.read(wav_path, dtype="float32")
        if data.ndim > 1:
            data = data.mean(axis=1)

        s = max(0, int(start_sec * sr))
        e = min(len(data), int(end_sec * sr))
        if s >= e:
            return None, "❌ 起始時間必須小於結束時間"

        segment = data[s:e]
        max_v = np.abs(segment).max()
        if max_v > 0:
            segment = segment / max_v
        seg_i16 = np.clip(segment * 32767, -32768, 32767).astype(np.int16)
        duration = (e - s) / sr
        return (sr, seg_i16), f"✅ 預覽區段 {start_sec:.1f}s → {end_sec:.1f}s  (時長 {duration:.2f}s)"
    except Exception as ex:
        return None, f"❌ {ex}"


def _save_segment(
    wav_path: str | None,
    start_sec: float,
    end_sec: float,
    template_name: str,
) -> tuple[str, list[str]]:
    """裁剪並儲存為 wav-template/{name}.wav。"""
    if not wav_path:
        return "❌ 請先下載音訊", _list_templates()
    if not template_name.strip():
        return "❌ 請輸入範本名稱", _list_templates()
    try:
        data, sr = sf.read(wav_path, dtype="float32")
        if data.ndim > 1:
            data = data.mean(axis=1)

        s = max(0, int(start_sec * sr))
        e = min(len(data), int(end_sec * sr))
        if s >= e:
            return "❌ 起始時間必須小於結束時間", _list_templates()

        segment = data[s:e]
        out_dir = _ensure_template_dir()
        safe_name = _sanitize_filename(template_name.strip())
        out_path = out_dir / f"{safe_name}.wav"
        sf.write(str(out_path), segment, sr)
        duration = (e - s) / sr
        return (
            f"✅ 已儲存：`wav-template/{safe_name}.wav`  (時長 {duration:.2f}s)",
            _list_templates(),
        )
    except Exception as ex:
        return f"❌ {ex}", _list_templates()


def _list_templates() -> list[str]:
    """列出 wav-template/ 下所有 WAV 檔。"""
    d = WAV_TEMPLATE_DIR
    if not d.exists():
        return []
    return sorted(str(p) for p in d.glob("*.wav"))


def _delete_template(template_path: str) -> tuple[str, list[str]]:
    """刪除指定範本檔。"""
    try:
        Path(template_path).unlink(missing_ok=True)
        return f"🗑️ 已刪除：{Path(template_path).name}", _list_templates()
    except Exception as ex:
        return f"❌ {ex}", _list_templates()


def build_youtube_tab() -> dict[str, Any]:
    """YouTube / 影片音訊提取分頁。"""
    components: dict[str, Any] = {}

    with gr.Tab("🎬 音訊提取") as tab:
        components["tab_youtube"] = tab

        gr.HTML("""
        <div style="padding:16px 0 8px">
          <div style="font-size:17px;font-weight:700;color:#e2e6ff;margin-bottom:4px">
            🎬 影片音訊提取 → 聲音範本
          </div>
          <div style="font-size:13px;color:#8b92b8">
            從 YouTube、BiliBili 等平台下載影片並提取音訊，
            選取特定區段儲存為聲音克隆範本（<code>wav-template/</code>）
          </div>
        </div>
        """)

        # ── Step 1：下載 ────────────────────────────────────────────────────
        with gr.Group():
            gr.HTML('<div style="font-size:14px;font-weight:600;color:#7aa3ff;padding:8px 0 4px">① 輸入影片 URL</div>')

            with gr.Row():
                url_input = gr.Textbox(
                    label="影片 URL",
                    placeholder="https://www.youtube.com/watch?v=... 或任何 yt-dlp 支援的網址",
                    scale=5,
                    container=True,
                )
                download_btn = gr.Button("⬇️ 下載音訊", variant="primary", scale=1, min_width=140)

            download_status = gr.Markdown("_請輸入 URL 後點擊下載_")
            wav_path_state = gr.State(value=None)
            duration_state = gr.State(value=0.0)

            full_audio = gr.Audio(label="完整音訊（可播放確認）", type="numpy", interactive=False)
            audio_info = gr.Markdown("")

        # ── Step 2：選取區段 ────────────────────────────────────────────────
        with gr.Group():
            gr.HTML('<div style="font-size:14px;font-weight:600;color:#7aa3ff;padding:8px 0 4px">② 選取要保存的區段</div>')
            gr.Markdown("_調整滑桿選取起始與結束時間，點擊預覽確認效果_")

            with gr.Row():
                start_slider = gr.Slider(
                    minimum=0, maximum=600, value=0, step=0.5,
                    label="起始時間（秒）", scale=2,
                )
                end_slider = gr.Slider(
                    minimum=0, maximum=600, value=10, step=0.5,
                    label="結束時間（秒）", scale=2,
                )
                preview_btn = gr.Button("▶ 預覽區段", variant="secondary", scale=1, min_width=120)

            segment_audio = gr.Audio(label="區段預覽", type="numpy", interactive=False)
            segment_status = gr.Markdown("")

        # ── Step 3：儲存範本 ────────────────────────────────────────────────
        with gr.Group():
            gr.HTML('<div style="font-size:14px;font-weight:600;color:#7aa3ff;padding:8px 0 4px">③ 儲存為聲音範本</div>')

            with gr.Row():
                template_name = gr.Textbox(
                    label="範本名稱（英文/數字/底線）",
                    placeholder="例：male_news_anchor 或 female_gentle",
                    scale=4,
                )
                save_btn = gr.Button("💾 儲存範本", variant="primary", scale=1, min_width=140)

            save_status = gr.Markdown("")
            gr.Markdown("---")

        # ── 範本清單 ────────────────────────────────────────────────────────
        with gr.Group():
            gr.HTML('<div style="font-size:14px;font-weight:600;color:#7aa3ff;padding:8px 0 4px">📂 已儲存的聲音範本</div>')

            with gr.Row():
                refresh_btn = gr.Button("🔄 重新整理", variant="secondary", scale=0, min_width=120)
                delete_input = gr.Textbox(
                    label="要刪除的檔案路徑（從清單複製）",
                    placeholder="wav-template/xxx.wav",
                    scale=3,
                )
                delete_btn = gr.Button("🗑️ 刪除", variant="secondary", scale=0, min_width=100)

            template_list = gr.Dataframe(
                headers=["檔案路徑"],
                datatype=["str"],
                value=[[p] for p in _list_templates()],
                label="聲音範本清單（可直接複製路徑到 Voice Clone Tab）",
                interactive=False,
            )
            delete_status = gr.Markdown("")

        # ── 事件綁定 ────────────────────────────────────────────────────────

        def on_download(url: str):
            wav_path, status = _download_audio(url)
            if wav_path:
                audio_data, duration, info = _read_audio(wav_path)
                new_end = min(10.0, duration)
                return (
                    status, wav_path, duration, audio_data, info,
                    gr.update(maximum=duration, value=0),
                    gr.update(maximum=duration, value=new_end),
                )
            return status, None, 0.0, None, "", gr.update(), gr.update()

        download_btn.click(
            fn=on_download,
            inputs=[url_input],
            outputs=[download_status, wav_path_state, duration_state,
                     full_audio, audio_info, start_slider, end_slider],
        )

        preview_btn.click(
            fn=_crop_and_preview,
            inputs=[wav_path_state, start_slider, end_slider],
            outputs=[segment_audio, segment_status],
        )

        save_btn.click(
            fn=_save_segment,
            inputs=[wav_path_state, start_slider, end_slider, template_name],
            outputs=[save_status, template_list],
        )

        refresh_btn.click(
            fn=lambda: [[p] for p in _list_templates()],
            outputs=[template_list],
        )

        delete_btn.click(
            fn=lambda path: (
                *(_delete_template(path) if path.strip() else ("❌ 請輸入檔案路徑", _list_templates())),
            ),
            inputs=[delete_input],
            outputs=[delete_status, template_list],
        )

    return components
