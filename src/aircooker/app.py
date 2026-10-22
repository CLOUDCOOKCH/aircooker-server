"""Keep already deployed uvicorn commands working during the Mealf migration."""

from mealf.app import create_app

__all__ = ["create_app"]
