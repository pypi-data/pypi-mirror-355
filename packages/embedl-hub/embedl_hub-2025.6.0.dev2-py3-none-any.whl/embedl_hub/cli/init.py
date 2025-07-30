# Copyright (C) 2025 Embedl AB
"""
Project and experiment context management for embedl-hub CLI.

This module provides CLI commands to initialize and display the current project
and experiment context. The selected context determines under which project and
experiment all data, results, and metadata are stored in the user's account on
https://hub.embedl.com.

Users can create new projects and experiments, switch between them, and view the
active context. Context information is stored locally in a YAML file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import typer
import yaml
from rich.table import Table

from embedl_hub.core.hub_logging import console
from embedl_hub.tracking import set_experiment, set_project
from embedl_hub.tracking.utils import (
    timestamp_id,
    to_experiment_url,
)

CTX_FILE = Path(".embedl_hub_ctx")

init_cli = typer.Typer(help="Initialise / show project & experiment context")


def read_embedl_hub_context() -> Dict[str, str]:
    """Read the current embedl-hub context from the local YAML file."""
    return (
        yaml.safe_load(CTX_FILE.read_text(encoding="utf-8"))
        if CTX_FILE.exists()
        else {}
    )


def _write_ctx(ctx: Dict[str, str]) -> None:
    CTX_FILE.write_text(yaml.safe_dump(ctx, sort_keys=False), encoding="utf-8")


def _set_new_experiment(ctx: dict, experiment: str | None = None) -> None:
    """Set a new experiment in the context dict, using the given name or a generated one."""
    experiment_name = experiment or timestamp_id("experiment")
    experiment_ctx = set_experiment(experiment_name)
    ctx["experiment_id"] = experiment_ctx.id
    ctx["experiment_name"] = experiment_ctx.name


@init_cli.command("init")
def init(
    project: Optional[str] = typer.Option(
        None, "-p", "--project", help="Project name or id", show_default=False
    ),
    experiment: Optional[str] = typer.Option(
        None,
        "-e",
        "--experiment",
        help="Experiment name or id",
        show_default=False,
    ),
):
    """
    Create new or load existing project and/or experiment.

    Examples
    --------
    Create new project and experiment (random names):

        $ embedl-hub init

    Create new or load existing project called `MyProj`:

        $ embedl-hub init -p MyProj

    Create new or load existing experiment `MyExp` inside the current project (omit name for random ID):

        $ embedl-hub init -e MyExp

    Create new or load existing project and experiment with names `MyProj` and `MyExp` (omit names for random IDs):

        $ embedl-hub init -p MyProj -e MyExp

    """

    ctx = (
        {}
        if project is None and experiment is None
        else read_embedl_hub_context()
    )

    if experiment and not (project or ctx):
        console.print(
            "[red]✗[/] No project initialized; run with --project first"
        )
        raise typer.Exit(1)

    # Set or switch project if needed
    if project is not None or not ctx:
        project_name = project or timestamp_id("project")
        project_ctx = set_project(project_name)
        ctx = {  # Reset context on new project
            "project_id": project_ctx.id,
            "project_name": project_ctx.name,
        }
        # Always set a new experiment when a new project is created or switched to
        _set_new_experiment(ctx, experiment)
    elif "project_id" in ctx and "project_name" in ctx:
        set_project(ctx["project_name"])
        # Set experiment if given, or if missing in context
        if experiment or "experiment_id" not in ctx:
            _set_new_experiment(ctx, experiment)
    else:
        console.print(
            "[red]✗[/] No project initialised, run `embedl-hub init -p <name>` first."
        )
        raise typer.Exit(1)

    _write_ctx(ctx)

    console.print(f"[green]✓ Project:[/] {ctx['project_name']}")
    console.print(f"[green]✓ Experiment:[/] {ctx['experiment_name']}")
    console.print(
        f"See your results: {to_experiment_url(ctx['project_id'], ctx['experiment_id'])}"
    )

    if project is not None and experiment is None:
        console.print(
            "[yellow]Note:[/] A new experiment was created because no experiment name was specified. To continue an existing experiment, use -e <experiment>."
        )


@init_cli.command("show")
def show():
    """Print active project/experiment IDs and names."""
    ctx = read_embedl_hub_context()
    table = Table(title=".embedl_hub_ctx", show_lines=True, show_header=False)
    for k in (
        "project_id",
        "project_name",
        "experiment_id",
        "experiment_name",
    ):
        table.add_row(k, ctx.get(k, "—"))
    console.print(table)
