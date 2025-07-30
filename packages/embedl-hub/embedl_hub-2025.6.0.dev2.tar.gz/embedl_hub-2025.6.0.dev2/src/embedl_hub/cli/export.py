# Copyright (C) 2025 Embedl AB

"""
embedl-hub export - send torch script model to Qualcomm AI Hub and retrieve an onnx model.
"""

from pathlib import Path
from typing import Optional, Tuple

import typer

from embedl_hub.core.compile import CompileError, compile_model
from embedl_hub.core.hardware.qualcomm_ai_hub import print_device_table
from embedl_hub.core.hub_logging import console

export_cli = typer.Typer(
    invoke_without_command=True,
    no_args_is_help=True,
)


def _prepare_image_size(size: str) -> Optional[Tuple[int, int]]:
    if not size:
        return None
    try:
        height, width = map(int, size.split(","))
    except ValueError as error:
        raise ValueError(
            "Invalid size format. Use height,width, e.g. 224,224"
        ) from error
    console.print(f"[yellow]Using input image size: {size}[/]")
    return height, width


@export_cli.command()
def export(
    model: Path = typer.Option(
        ...,
        "-m",
        "--model",
        help="Path to the TorchScript model file to be exported.",
        show_default=False,
    ),
    size: str = typer.Option(
        ...,
        "--size",
        "-s",
        help="Input image size in format HEIGHT,WIDTH (e.g. 224,224).",
        show_default=False,
    ),
    device: str = typer.Option(
        None,
        "-d",
        "--device",
        help="Target device name. Run `embedl-hub list-devices` to see options. Exporting for a specific device can improve compatibility.",
        show_default=False,
    ),
    output_file: str = typer.Option(
        None,
        "-o",
        "--output-file",
        help="Destination path or directory to save the exported model.",
        show_default=False,
    ),
):
    """
    Compile a TorchScript model into an ONNX model using Qualcomm AI Hub.

    Required arguments:
        --model
        --size

    Examples
    --------
    Export the TorchScript model `tuned_model.pt` with input size 224x224:

        $ embedl-hub export -m tuned_model.pt --size 224,224

    Export the TorchScript model `tuned_model.pt` with input size 224x224 and save it to `./my_outputs/model.onnx`:

        $ embedl-hub export -m tuned_model.pt  --size 224,224 -o ./my_outputs/model.onnx

    """

    if not model:
        raise ValueError("Please specify a model to export using --model")
    if not size:
        raise ValueError(
            "Please specify input image size using --size, e.g. 224,224"
        )
    if not output_file:
        output_file = model.with_suffix(".onnx").as_posix()
        console.print(
            f"[yellow]No output file specified, using {output_file}[/]"
        )
    image_size = _prepare_image_size(size)
    try:
        compile_model(
            model_file=model,
            device=device,
            runtime="onnx",
            quantize_io=False,
            output_file=output_file,
            image_size=image_size,
        )
        console.print("[green]✓ Exported model to ONNX[/]")

        # TODO: upload artifacts / metrics to web
    except (CompileError, ValueError) as error:
        console.print(f"[red]✗ {error}[/]")
        raise typer.Exit(1)
