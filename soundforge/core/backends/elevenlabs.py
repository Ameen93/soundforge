"""ElevenLabs Sound Effects API backend."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Callable

import httpx
import numpy as np
import soundfile as sf

from soundforge.core.backends import GenerationBackend

if TYPE_CHECKING:
    from soundforge.core.config import SoundForgeConfig

API_BASE = "https://api.elevenlabs.io"
GENERATE_ENDPOINT = "/v1/sound-generation"
MODEL_ID = "eleven_text_to_sound_v2"
# Request PCM at 44100 Hz for maximum quality and easy numpy conversion
OUTPUT_FORMAT = "mp3_44100_128"
TIMEOUT = 60


class ElevenLabsBackend(GenerationBackend):
    """ElevenLabs Sound Effects API backend."""

    def __init__(self, config: SoundForgeConfig) -> None:
        self._api_key = config.elevenlabs_api_key

    def generate(
        self,
        text: str,
        duration_seconds: float | None = None,
        loop: bool = False,
        prompt_influence: float = 0.3,
        seed: int | None = None,
        on_status: Callable[[str], None] | None = None,
    ) -> tuple[np.ndarray, int]:
        """Generate audio via ElevenLabs API. Returns (samples, sample_rate)."""
        if not self._api_key:
            raise RuntimeError(
                "ElevenLabs API key not configured. "
                "Set ELEVENLABS_API_KEY env var or run 'soundforge setup'."
            )

        if on_status:
            on_status(f"Generating: {text[:60]}...")

        max_duration = self.capabilities()["max_duration"]

        body: dict = {
            "text": text,
            "model_id": MODEL_ID,
            "prompt_influence": prompt_influence,
        }
        if duration_seconds is not None:
            clamped = max(0.5, min(float(max_duration), duration_seconds))
            if clamped != duration_seconds and on_status:
                on_status(
                    f"Warning: duration {duration_seconds}s clamped to "
                    f"{clamped}s (backend max: {max_duration}s)"
                )
            body["duration_seconds"] = clamped
        if loop:
            body["loop"] = True

        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
        }

        url = f"{API_BASE}{GENERATE_ENDPOINT}?output_format={OUTPUT_FORMAT}"

        try:
            response = httpx.post(
                url, json=body, headers=headers, timeout=TIMEOUT
            )
        except httpx.TimeoutException:
            raise RuntimeError(
                "ElevenLabs API request timed out. Check your network connection."
            )
        except httpx.ConnectError:
            raise RuntimeError(
                "Could not connect to ElevenLabs API. Check your network connection."
            )

        if response.status_code != 200:
            code = response.status_code
            if code == 401:
                raise RuntimeError(
                    "Invalid or expired API key. "
                    "Verify at elevenlabs.io/app/settings/api-keys"
                )
            elif code == 429:
                raise RuntimeError(
                    "Rate limit exceeded. Wait a moment and retry, "
                    "or upgrade your plan."
                )
            elif code >= 500:
                raise RuntimeError(
                    "ElevenLabs server error. Try again in a few minutes."
                )
            else:
                detail = response.text[:200] if response.text else "No details"
                raise RuntimeError(
                    f"ElevenLabs API error (HTTP {code}): {detail}"
                )

        if on_status:
            on_status("Decoding audio...")

        # Response is binary audio data (MP3)
        audio_bytes = response.content
        samples, sample_rate = sf.read(io.BytesIO(audio_bytes))

        # Ensure float64 for processing consistency
        samples = samples.astype(np.float64)

        if on_status:
            duration = len(samples) / sample_rate
            on_status(f"Generated {duration:.1f}s audio at {sample_rate} Hz")

        return samples, sample_rate

    def is_available(self) -> bool:
        return bool(self._api_key)

    def info(self) -> dict:
        return {
            "name": "elevenlabs",
            "model": MODEL_ID,
            "api_base": API_BASE,
            "available": self.is_available(),
            "status": "ready" if self.is_available() else "API key not configured",
        }

    def capabilities(self) -> dict:
        return {
            "max_duration": 30,
            "supports_loop": True,
            "supports_seed": False,
        }
