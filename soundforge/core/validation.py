"""Preflight validation for backend-driven generation requests."""

from __future__ import annotations

from typing import Callable


def validate_generation_request(
    *,
    backend_name: str,
    capabilities: dict,
    duration: float | None,
    loop: bool,
    on_status: Callable[[str], None] | None = None,
) -> float | None:
    """Validate and normalize generation parameters before backend calls."""
    normalized_duration = duration

    max_duration = capabilities.get("max_duration")
    if (
        normalized_duration is not None
        and max_duration is not None
        and normalized_duration > float(max_duration)
    ):
        if on_status:
            on_status(
                f"Warning: requested duration {normalized_duration}s exceeds "
                f"backend '{backend_name}' max of {max_duration}s; clamping to "
                f"{max_duration}s"
            )
        normalized_duration = float(max_duration)

    if loop and not capabilities.get("supports_loop", False):
        raise RuntimeError(
            f"Backend '{backend_name}' does not support loop generation. "
            "Choose a loop-capable backend or disable loop mode."
        )

    return normalized_duration
