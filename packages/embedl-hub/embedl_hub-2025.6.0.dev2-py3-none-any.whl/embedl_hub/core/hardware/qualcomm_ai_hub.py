# Copyright (C) 2025 Embedl AB

"""
Functionality for handling the Qualcomm AI Hub communication and device management.
"""

import qai_hub as hub
from rich.table import Table

from embedl_hub.core.hub_logging import console


def print_device_table():
    """Print a table of available devices on the Qualcomm AI Hub."""
    table = Table(title="Embedl Hub devices")
    table.add_column("Name", style="cyan")
    table.add_column("Provider")
    table.add_column("OS")
    table.add_column("Chipset / Attrs", overflow="fold")
    for d in hub.get_devices():
        feats = ", ".join(a for a in d.attributes if "chipset" in a)
        table.add_row(d.name, "qai_hub", d.os or "—", feats or "—")
    console.print(table)
