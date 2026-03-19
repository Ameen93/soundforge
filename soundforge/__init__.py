"""SoundForge — AI-powered game audio asset generator."""

__version__ = "0.1.0"

from soundforge.core.batch import batch_generate
from soundforge.core.generate import generate
from soundforge.core.types import (
    AssetType,
    AudioAsset,
    BatchResult,
    Engine,
    GenerateResult,
    InfoResult,
    InspectResult,
)

__all__ = [
    "__version__",
    "generate",
    "batch_generate",
    "AssetType",
    "AudioAsset",
    "BatchResult",
    "Engine",
    "GenerateResult",
    "InfoResult",
    "InspectResult",
]
