# Copyright (C) 2025 Embedl AB

from typing import Any, Dict


def remove_none_values(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Remove keys with None values from a dictionary."""
    return {key: val for key, val in input_dict.items() if val is not None}
