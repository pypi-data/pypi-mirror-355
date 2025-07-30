# Copyright (C) 2025 Embedl AB
"""CLI command to benchmark a model's performance on a device.

This command profiles the latency of a compiled model on a specified device
and saves the results in JSON format. Both a summary and a full profile
are generated and saved to the specified output directory. The full profile
includes detailed performance metrics useful for debugging.
"""

import json
from datetime import datetime
from pathlib import Path

import typer

from embedl_hub.cli.init import read_embedl_hub_context
from embedl_hub.core.benchmark import (
    ProfileError,
    print_profile_summary,
    profile_model,
)
from embedl_hub.core.hub_logging import console

benchmark_cli = typer.Typer(
    help="Profile latency on device",
    no_args_is_help=True,
)


@benchmark_cli.command()
def benchmark(
    model: Path = typer.Option(
        ...,
        "-m",
        "--model",
        help="Path to compiled model file (.tflite, .onnx, or .bin)",
        show_default=False,
    ),
    device: str = typer.Option(
        ..., "-d", "--device", help="Device name", show_default=False
    ),
    output_dir: Path = typer.Option(
        None, "--output-dir", "-o", help="Output folder for profile JSONs"
    ),
):
    """Profile compiled model on device and measure it's performance.

    Examples:
    ---------
    Profile a .tflite model on Samsung Galaxy S25 and save results to
    the default profiles folder:

        $ embedl-hub profile -m my_model.tflite -d "Samsung Galaxy S25"

    Profile an .onnx model on Samsung Galaxy 8 Elite QRD and save
    results to a custom output directory:

        $ embedl-hub profile -m my_model.onnx -d "Samsung Galaxy 8 Elite QRD" -o results/

    """

    ctx = read_embedl_hub_context()

    console.log(f"profiling {model.name} on {device} using Qualcomm AI Hub")
    try:
        summary, full = profile_model(
            model,
            device,
            project_name=ctx["project_name"],
            experiment_name=ctx["experiment_name"],
        )
    except ProfileError as e:
        console.print(f"[red]✗ profiling failed:[/] {e}")
        raise typer.Exit(1)
    print_profile_summary(summary)

    if output_dir is None:
        outdir = Path("profiles")
    else:
        outdir = Path(output_dir)
    outdir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = outdir / f"{model.stem}_{ts}.json"
    full_path = outdir / f"{model.stem}_{ts}.full.json"

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    console.print(f"[green]✓ Saved profile summary to:[/] {summary_path}")

    with open(full_path, "w") as f:
        json.dump(full, f, indent=2)
    console.print(
        f"[green]✓ Saved full Qualcomm AI Hub profile to:[/] {full_path}"
    )
