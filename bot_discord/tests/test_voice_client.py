import time
from unittest.mock import MagicMock

from bot_discord.modules.voice_client import VoiceHandler


def test_can_be_interrupted_false_without_voice_client():
    bot = MagicMock()
    bot.voice_clients = []
    handler = VoiceHandler(bot, voice_engine=MagicMock())
    assert handler.can_be_interrupted() is False


def test_can_be_interrupted_true_when_playing():
    bot = MagicMock()
    voice_client = MagicMock()
    voice_client.is_playing.return_value = True
    bot.voice_clients = [voice_client]
    handler = VoiceHandler(bot, voice_engine=MagicMock())
    handler.last_audio_start_time = time.time() - 1.0
    assert handler.can_be_interrupted() is True
