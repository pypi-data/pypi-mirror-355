# Copyright (C) 2025 Embedl AB
"""
On-device profiling of models via Qualcomm AI Hub.
This module provides functionality to profile model latency and memory usage
on a target device, returning detailed execution statistics.
"""

from pathlib import Path

import qai_hub as hub

from embedl_hub.core.context import experiment_context
from embedl_hub.core.hub_logging import console
from embedl_hub.tracking import RunType, log_metric, log_param


class ProfileError(RuntimeError):
    pass


def _to_ms(val):
    "Always return milliseconds as float, or None if not available."
    return float(val) / 1000.0 if val is not None else None


def _count_layers_by_unit(execution_detail):
    counts = {"CPU": 0, "GPU": 0, "NPU": 0}
    for layer in execution_detail:
        unit = layer.get("compute_unit")
        if unit in counts:
            counts[unit] += 1
    return counts


def _to_megabytes(val):
    "Convert bytes to megabytes as float, or None if not available."
    return float(val) / (1024 * 1024) if val is not None else None


def _log_metrics(summary: dict) -> None:
    """Log profiling metrics to the tracking system."""
    log_metric(
        "latency",
        summary.get("mean_ms"),
    )
    log_metric(
        "peak_memory_usage_mb",
        summary.get("peak_memory_usage_mb"),
    )
    for unit, count in summary.get("layers_by_unit", {}).items():
        log_metric(
            f"layers_{unit.lower()}",
            count,
        )


def profile_model(
    model: Path,
    device: str,
    project_name: str = None,
    experiment_name: str = None,
) -> tuple[dict, dict]:
    """
    Profile model latency on a target device using Qualcomm AI Hub.
    Returns (summary_dict, full_profile_dict).
    Raises ProfileError on failure.
    """
    with experiment_context(
        project_name=project_name,
        experiment_name=experiment_name,
        run_type=RunType.BENCHMARK,
    ):

        try:
            dev = hub.Device(device)
            job = hub.submit_profile_job(model=model, device=dev)
            prof = job.download_profile()
        except Exception as exc:
            raise ProfileError("Failed to submit profile job.") from exc

        log_param("device", device)

        summary = prof.get("execution_summary", {})
        execution_detail = prof.get("execution_detail", [])
        layer_counts = _count_layers_by_unit(execution_detail)
        summary_dict = {
            "mean_ms": _to_ms(summary.get("estimated_inference_time")),
            "peak_memory_usage_mb": _to_megabytes(
                summary.get("estimated_inference_peak_memory")
            ),
            "layers": prof.get("layers", []),
            "layers_by_unit": layer_counts,
        }
        _log_metrics(summary_dict)
        return summary_dict, prof


def print_profile_summary(summary: dict) -> None:
    """Print latency summary to the user in a consistent way."""
    if summary.get("mean_ms") is not None:
        console.print(f"[green]✓ Mean latency:[/] {summary['mean_ms']:.2f} ms")
    if summary.get("peak_memory_usage_mb") is not None:
        console.print(
            f"[green]✓ Peak memory usage:[/] {summary['peak_memory_usage_mb']:.2f} MB"
        )
    if summary.get("layers_by_unit"):
        units = summary["layers_by_unit"]
        console.print(
            f"[green]✓ Layers by compute unit:[/] NPU={units['NPU']}, GPU={units['GPU']}, CPU={units['CPU']}"
        )
