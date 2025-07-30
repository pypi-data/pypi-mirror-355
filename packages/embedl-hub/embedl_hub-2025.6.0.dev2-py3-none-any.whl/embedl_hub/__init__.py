# Copyright (C) 2025 Embedl AB

"""
Public Embedl Hub library API.
```pycon
>>> import embedl_hub
>>> embedl_hub.__version__
'2025.6.0'
```
"""

__all__ = []
try:
    from importlib.metadata import version as _v

    __version__ = _v(__name__)
except Exception:
    __version__ = "2025.6.0.dev2"
