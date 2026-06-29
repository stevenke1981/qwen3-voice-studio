"""Tests for src.monitor — SystemMetrics, format_metrics_display."""

from __future__ import annotations

import pytest

from src.monitor import SystemMetrics, format_metrics_display, get_system_metrics


class TestSystemMetrics:
    """SystemMetrics dataclass 測試."""

    def test_defaults(self) -> None:
        m = SystemMetrics()
        assert m.gpu_name == "N/A"
        assert m.gpu_utilization == 0.0
        assert m.gpu_memory_used_mb == 0.0
        assert m.gpu_memory_total_mb == 0.0
        assert m.cpu_percent == 0.0
        assert m.ram_used_mb == 0.0
        assert m.ram_total_mb == 0.0
        assert not m.model_loaded
        assert m.last_latency_ms == 0.0

    def test_custom_values(self) -> None:
        m = SystemMetrics(
            gpu_name="RTX 3060 Ti",
            gpu_utilization=45.5,
            gpu_memory_used_mb=2048.0,
            gpu_memory_total_mb=8192.0,
            cpu_percent=32.1,
            ram_used_mb=4096.0,
            ram_total_mb=16384.0,
            model_loaded=True,
            last_latency_ms=123.4,
        )
        assert m.gpu_name == "RTX 3060 Ti"
        assert m.gpu_utilization == 45.5
        assert m.model_loaded
        assert m.last_latency_ms == 123.4

    def test_frozen(self) -> None:
        m = SystemMetrics()
        with pytest.raises(AttributeError):
            m.gpu_name = "Other"  # type: ignore[misc]


class TestFormatMetricsDisplay:
    """format_metrics_display 測試."""

    @pytest.fixture()  # type: ignore[misc]
    def sample_metrics(self) -> SystemMetrics:
        return SystemMetrics(
            gpu_name="RTX 3060 Ti",
            gpu_utilization=50.0,
            gpu_memory_used_mb=2048.0,
            gpu_memory_total_mb=8192.0,
            cpu_percent=25.0,
            ram_used_mb=4096.0,
            ram_total_mb=16384.0,
            model_loaded=True,
            last_latency_ms=100.0,
        )

    def test_zh_tw_format(self, sample_metrics: SystemMetrics) -> None:
        output = format_metrics_display(sample_metrics, locale="zh-TW")
        assert "GPU 使用率" in output
        assert "50.0%" in output
        assert "2048" in output
        assert "8192" in output
        assert "已載入" in output
        assert "100.0 ms" in output

    def test_en_format(self, sample_metrics: SystemMetrics) -> None:
        output = format_metrics_display(sample_metrics, locale="en")
        assert "GPU Usage" in output
        assert "50.0%" in output
        assert "Loaded" in output
        assert "100.0 ms" in output

    def test_model_not_loaded(self) -> None:
        m = SystemMetrics(model_loaded=False)
        zh = format_metrics_display(m, locale="zh-TW")
        assert "未載入" in zh
        en = format_metrics_display(m, locale="en")
        assert "Not Loaded" in en

    def test_empty_metrics(self) -> None:
        m = SystemMetrics()
        output = format_metrics_display(m)
        assert "N/A" in output


class TestGetSystemMetrics:
    """get_system_metrics 測試（無 GPU / 無 psutil 時的 graceful fallback）."""

    def test_returns_system_metrics_instance(self) -> None:
        m = get_system_metrics()
        assert isinstance(m, SystemMetrics)

    def test_model_loaded_flag(self) -> None:
        m = get_system_metrics(model_loaded=True)
        assert m.model_loaded

    def test_last_latency_passthrough(self) -> None:
        m = get_system_metrics(last_latency=250.0)
        assert m.last_latency_ms == 250.0

    def test_no_gpu_fallback(self) -> None:
        """無 pynvml 時 GPU 資訊應為預設值."""
        m = get_system_metrics()
        # 可能沒有 GPU，但至少不應拋出
        assert isinstance(m.gpu_name, str)
