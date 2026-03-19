"""CLI output formatting — enforces stdout/stderr separation."""

import json
import sys
from typing import Callable


def status(message: str, quiet: bool = False) -> None:
    """Print status message to stderr. Suppressed if quiet=True."""
    if not quiet:
        print(message, file=sys.stderr)


def output_json(data: dict) -> None:
    """Print JSON result to stdout (the only thing that should go to stdout)."""
    print(json.dumps(data, indent=2, default=str))


def output_human(message: str) -> None:
    """Print human-readable message to stderr (never stdout)."""
    print(message, file=sys.stderr)


def make_status_callback(quiet: bool) -> Callable[[str], None] | None:
    """Create an on_status callback for core functions."""
    if quiet:
        return None
    return lambda msg: print(msg, file=sys.stderr)


def error_json(message: str, details: str | None = None) -> None:
    """Print a JSON error payload to stdout for agent consumption."""
    payload: dict = {"error": message}
    if details:
        payload["details"] = details
    print(json.dumps(payload, indent=2))
