# Copyright (C) 2025 Embedl AB

"""Context manager for managing the current experiment context."""

import logging
from contextlib import contextmanager

from embedl_hub.core.hub_logging import console
from embedl_hub.tracking import RunType, set_experiment, set_project, start_run
from embedl_hub.tracking.utils import to_run_url


@contextmanager
def experiment_context(
    project_name: str, experiment_name: str, run_type: RunType
):
    """
    Context manager for managing the current experiment context.
    """
    try:
        project = set_project(project_name)
        experiment = set_experiment(experiment_name)

        console.log(f"Running command with project name: {project_name}")
        console.log(f"Running command with experiment name: {experiment_name}")
        with start_run(type=run_type) as run:
            console.log(
                f"Track your progress at {to_run_url(project_id=project.id, experiment_id=experiment.id, run_id=run.id)}"
            )
            yield
            console.log(
                f"View results at {to_run_url(project_id=project.id, experiment_id=experiment.id, run_id=run.id)}"
            )
    finally:
        pass
