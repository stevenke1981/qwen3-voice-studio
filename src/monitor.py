"""Qwen3 Voice Studio — 效能監控."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SystemMetrics:
    """系統效能指標."""

    gpu_name: str = "N/A"
    gpu_utilization: float = 0.0
    gpu_memory_used_mb: float = 0.0
    gpu_memory_total_mb: float = 0.0
    cpu_percent: float = 0.0
    ram_used_mb: float = 0.0
    ram_total_mb: float = 0.0
    model_loaded: bool = False
    last_latency_ms: float = 0.0


def get_system_metrics(model_loaded: bool = False, last_latency: float = 0.0) -> SystemMetrics:
    """取得系統效能指標."""
    gpu_name = "N/A"
    gpu_util = 0.0
    gpu_mem_used = 0.0
    gpu_mem_total = 0.0

    try:
        import pynvml

        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(gpu_name, bytes):
            gpu_name = gpu_name.decode()
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        gpu_util = float(util.gpu)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        gpu_mem_used = mem.used / (1024 * 1024)
        gpu_mem_total = mem.total / (1024 * 1024)
        pynvml.nvmlShutdown()
    except Exception:
        pass

    cpu_pct = 0.0
    ram_used = 0.0
    ram_total = 0.0
    try:
        import psutil

        cpu_pct = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        ram_used = mem.used / (1024 * 1024)
        ram_total = mem.total / (1024 * 1024)
    except ImportError:
        pass

    return SystemMetrics(
        gpu_name=gpu_name,
        gpu_utilization=gpu_util,
        gpu_memory_used_mb=gpu_mem_used,
        gpu_memory_total_mb=gpu_mem_total,
        cpu_percent=cpu_pct,
        ram_used_mb=ram_used,
        ram_total_mb=ram_total,
        model_loaded=model_loaded,
        last_latency_ms=last_latency,
    )


def format_metrics_display(m: SystemMetrics, locale: str = "zh-TW") -> str:
    """格式化效能指標為顯示文字."""
    if locale == "zh-TW":
        lines = [
            f"🖥️ GPU: {m.gpu_name}",
            f"📊 GPU 使用率: {m.gpu_utilization:.1f}%",
            f"💾 GPU 記憶體: {m.gpu_memory_used_mb:.0f} / {m.gpu_memory_total_mb:.0f} MB",
            f"🔧 CPU: {m.cpu_percent:.1f}%",
            f"🧠 RAM: {m.ram_used_mb:.0f} / {m.ram_total_mb:.0f} MB",
            f"⚡ 延遲: {m.last_latency_ms:.1f} ms",
            f"🤖 模型: {'已載入' if m.model_loaded else '未載入'}",
        ]
    else:
        lines = [
            f"🖥️ GPU: {m.gpu_name}",
            f"📊 GPU Usage: {m.gpu_utilization:.1f}%",
            f"💾 GPU Memory: {m.gpu_memory_used_mb:.0f} / {m.gpu_memory_total_mb:.0f} MB",
            f"🔧 CPU: {m.cpu_percent:.1f}%",
            f"🧠 RAM: {m.ram_used_mb:.0f} / {m.ram_total_mb:.0f} MB",
            f"⚡ Latency: {m.last_latency_ms:.1f} ms",
            f"🤖 Model: {'Loaded' if m.model_loaded else 'Not Loaded'}",
        ]
    return "\n".join(lines)
