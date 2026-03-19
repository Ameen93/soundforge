"""Backend interface and factory for SoundForge generation backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable

import numpy as np

if TYPE_CHECKING:
    from soundforge.core.config import SoundForgeConfig


class GenerationBackend(ABC):
    """Base interface for audio generation backends."""

    @abstractmethod
    def generate(
        self,
        text: str,
        duration_seconds: float | None = None,
        loop: bool = False,
        prompt_influence: float = 0.3,
        seed: int | None = None,
        on_status: Callable[[str], None] | None = None,
    ) -> tuple[np.ndarray, int]:
        """Generate audio from text. Returns (samples, sample_rate)."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is ready (API key set, etc.)."""
        ...

    @abstractmethod
    def info(self) -> dict:
        """Return backend status and configuration."""
        ...

    def capabilities(self) -> dict:
        """Return what this backend supports."""
        return {
            "max_duration": 30,
            "supports_loop": False,
            "supports_seed": False,
        }


def get_backend(name: str, config: SoundForgeConfig) -> GenerationBackend:
    """Factory function to get a backend by name."""
    if name == "elevenlabs":
        from soundforge.core.backends.elevenlabs import ElevenLabsBackend

        return ElevenLabsBackend(config)
    if name == "stable-audio":
        from soundforge.core.backends.stable_audio import StableAudioBackend

        return StableAudioBackend(config)
    raise ValueError(f"Unknown backend: {name!r}. Available: elevenlabs, stable-audio")
