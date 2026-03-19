"""Tests for audio preview."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import soundfile as sf


class TestPlayFile:
    @patch.dict("sys.modules", {"sounddevice": MagicMock()})
    def test_plays_file(self, tmp_path):
        import sys

        mock_sd = sys.modules["sounddevice"]
        mock_sd.play = MagicMock()
        mock_sd.wait = MagicMock()

        # Create test WAV
        path = tmp_path / "test.wav"
        samples = np.sin(np.linspace(0, 2 * np.pi * 440, 4410))
        sf.write(str(path), samples, 44100, subtype="PCM_16")

        # Need to reimport to pick up the mock
        from soundforge.core.preview import play_file

        play_file(path)

        mock_sd.play.assert_called_once()
        mock_sd.wait.assert_called_once()
        # Verify correct sample rate passed
        call_args = mock_sd.play.call_args
        assert call_args[0][1] == 44100

    @patch.dict("sys.modules", {"sounddevice": MagicMock()})
    def test_play_array(self):
        import sys

        mock_sd = sys.modules["sounddevice"]
        mock_sd.play = MagicMock()
        mock_sd.wait = MagicMock()

        from soundforge.core.preview import play_array

        samples = np.zeros(100)
        play_array(samples, 22050)

        mock_sd.play.assert_called_once()
        mock_sd.wait.assert_called_once()
        call_args = mock_sd.play.call_args
        assert call_args[0][1] == 22050


class TestMissingSounddevice:
    def test_play_file_without_sounddevice(self, tmp_path):
        # Create test WAV
        path = tmp_path / "test.wav"
        samples = np.sin(np.linspace(0, 2 * np.pi * 440, 4410))
        sf.write(str(path), samples, 44100, subtype="PCM_16")

        # Simulate missing sounddevice by patching the import
        with patch.dict("sys.modules", {"sounddevice": None}):
            # Need to reload to trigger the import failure
            import importlib
            import soundforge.core.preview as preview_mod

            importlib.reload(preview_mod)

            with pytest.raises(RuntimeError, match="sounddevice is required"):
                preview_mod.play_file(path)

            # Restore
            importlib.reload(preview_mod)

    def test_play_array_without_sounddevice(self):
        with patch.dict("sys.modules", {"sounddevice": None}):
            import importlib
            import soundforge.core.preview as preview_mod

            importlib.reload(preview_mod)

            with pytest.raises(RuntimeError, match="sounddevice is required"):
                preview_mod.play_array(np.zeros(100), 44100)

            importlib.reload(preview_mod)
