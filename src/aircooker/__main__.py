"""Deprecated entry point; new deployments use python -m mealf."""

import runpy

runpy.run_module("mealf", run_name="__main__")
