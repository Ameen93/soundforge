"""Stable Audio Open local generation backend."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import numpy as np

from soundforge.core.backends import GenerationBackend

if TYPE_CHECKING:
    from soundforge.core.config import SoundForgeConfig

MODEL_ID = "stabilityai/stable-audio-open-1.0"
DEFAULT_NEGATIVE_PROMPT = "low quality, distorted, noise"
DEFAULT_GUIDANCE_SCALE = 7.0
SAMPLE_RATE = 44100
MAX_DURATION = 47.0


class StableAudioBackend(GenerationBackend):
    """Local GPU backend using Stable Audio Open 1.0 via diffusers."""

    def __init__(self, config: SoundForgeConfig) -> None:
        self._settings = config._backend_settings.get("stable-audio", {})
        self._model_path = self._settings.get("model_path", MODEL_ID)
        self._negative_prompt = self._settings.get(
            "negative_prompt", DEFAULT_NEGATIVE_PROMPT
        )
        self._guidance_scale = float(
            self._settings.get("guidance_scale", DEFAULT_GUIDANCE_SCALE)
        )
        self._fixed_steps: int | None = (
            int(self._settings["num_inference_steps"])
            if "num_inference_steps" in self._settings
            else None
        )
        self._pipe = None
        self._torch = None

    def _load_pipeline(
        self, on_status: Callable[[str], None] | None = None
    ) -> None:
        """Lazy-load the diffusion pipeline on first use."""
        if self._pipe is not None:
            return

        try:
            import torch
            from diffusers import StableAudioPipeline
        except ImportError:
            raise RuntimeError(
                "Stable Audio backend requires torch and diffusers. "
                "Install with: pip install soundforge[local-gpu]"
            )

        if not torch.cuda.is_available():
            raise RuntimeError(
                "Stable Audio backend requires a CUDA GPU. "
                "No CUDA device found."
            )

        self._torch = torch

        if on_status:
            on_status(
                "Loading Stable Audio Open model "
                "(first run downloads ~4GB)..."
            )

        self._pipe = StableAudioPipeline.from_pretrained(
            self._model_path, torch_dtype=torch.float16
        )
        self._pipe = self._pipe.to("cuda")

        if on_status:
            on_status("Model loaded.")

    def _map_steps(self, prompt_influence: float) -> int:
        """Map prompt_influence 0.0-1.0 to inference steps 50-200."""
        if self._fixed_steps is not None:
            return self._fixed_steps
        clamped = max(0.0, min(1.0, prompt_influence))
        return int(50 + clamped * 150)

    def generate(
        self,
        text: str,
        duration_seconds: float | None = None,
        loop: bool = False,
        prompt_influence: float = 0.3,
        seed: int | None = None,
        on_status: Callable[[str], None] | None = None,
    ) -> tuple[np.ndarray, int]:
        """Generate audio locally via Stable Audio Open. Returns (samples, sample_rate)."""
        self._load_pipeline(on_status)
        torch = self._torch

        duration = float(duration_seconds or 5.0)
        if duration > MAX_DURATION:
            if on_status:
                on_status(
                    f"Warning: duration {duration}s clamped to "
                    f"{MAX_DURATION}s (model max)"
                )
            duration = MAX_DURATION

        steps = self._map_steps(prompt_influence)

        prompt = text
        if loop:
            prompt = f"seamless loop, {text}"

        if on_status:
            on_status(f"Generating ({steps} steps, {duration:.1f}s): {text[:60]}...")

        generator = torch.Generator(device="cuda")
        if seed is not None:
            generator.manual_seed(seed)

        try:
            result = self._pipe(
                prompt,
                negative_prompt=self._negative_prompt,
                num_inference_steps=steps,
                audio_end_in_s=duration,
                num_waveforms_per_prompt=1,
                guidance_scale=self._guidance_scale,
                generator=generator,
            )
        except torch.cuda.OutOfMemoryError:
            raise RuntimeError(
                "GPU out of memory during generation. "
                "Try a shorter duration or close other GPU applications."
            )

        # result.audios shape: (batch, channels, samples)
        audio_tensor = result.audios[0]  # (channels, samples)
        samples = audio_tensor.float().cpu().numpy().T  # (samples, channels)
        samples = samples.astype(np.float64)

        if on_status:
            actual_duration = len(samples) / SAMPLE_RATE
            on_status(f"Generated {actual_duration:.1f}s stereo audio at {SAMPLE_RATE} Hz")

        return samples, SAMPLE_RATE

    def is_available(self) -> bool:
        """Check if torch, diffusers, and CUDA are available."""
        try:
            import torch

            if not torch.cuda.is_available():
                return False
            import diffusers  # noqa: F401

            return True
        except ImportError:
            return False

    def info(self) -> dict:
        """Return backend status and GPU info."""
        available = self.is_available()
        if available:
            import torch

            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = round(
                torch.cuda.get_device_properties(0).total_memory / (1024**3), 1
            )
            return {
                "name": "stable-audio",
                "model": self._model_path,
                "available": True,
                "status": "ready",
                "gpu": gpu_name,
                "vram_gb": vram_gb,
            }
        return {
            "name": "stable-audio",
            "model": self._model_path,
            "available": False,
            "status": "torch/diffusers not installed or no CUDA GPU",
        }

    def capabilities(self) -> dict:
        """Return what this backend supports."""
        return {
            "max_duration": 47,
            "supports_loop": False,
            "supports_seed": True,
        }
