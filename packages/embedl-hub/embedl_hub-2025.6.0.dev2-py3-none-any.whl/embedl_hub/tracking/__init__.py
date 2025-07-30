# Copyright (C) 2025 Embedl AB

from embedl_hub.tracking.client import Client as _Client
from embedl_hub.tracking.rest_api import RunType

_global_client = _Client()

set_project = _global_client.set_project
set_experiment = _global_client.set_experiment
start_run = _global_client.start_run
log_param = _global_client.log_param
log_metric = _global_client.log_metric

__all__ = [
    "set_project",
    "set_experiment",
    "start_run",
    "log_param",
    "log_metric",
    "RunType",
]
