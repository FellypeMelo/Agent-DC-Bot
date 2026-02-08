from unittest.mock import MagicMock

from bot_discord.core.voice_engine import BargeInEngine, VoiceEngine


def test_barge_in_engine_returns_false_without_model(monkeypatch):
    engine = BargeInEngine()
    engine.model = None
    assert engine.is_speech(audio_chunk=MagicMock(), threshold=0.5) is False


def test_voice_engine_is_loaded_false_by_default():
    config = MagicMock()
    engine = VoiceEngine(config)
    assert engine.is_loaded() is False
