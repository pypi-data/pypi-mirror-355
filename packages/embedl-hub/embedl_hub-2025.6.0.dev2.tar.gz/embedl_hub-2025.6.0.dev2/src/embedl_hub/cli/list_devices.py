# Copyright (C) 2025 Embedl AB
"""
embedl-hub list-devices - List all available target devices for the commands
`export`, `compile`, `quantize` and `benchmark`.
"""

import typer

from embedl_hub.core.hardware.qualcomm_ai_hub import print_device_table

list_devices_cli = typer.Typer()


@list_devices_cli.command()
def list_devices():
    """
    List all available target devices.

    A device name is used as input to the `--device` option
    in the commands `export`, `compile`, `quantize` and `benchmark`.
    """
    print_device_table()
