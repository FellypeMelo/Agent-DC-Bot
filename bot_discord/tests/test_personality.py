# test_personality.py

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import os
import sys

# Adiciona o diretório raiz ao path para importações relativas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from bot_discord.core.bot import DiscordBot

class TestPersonality(unittest.IsolatedAsyncioTestCase):

    @patch('bot_discord.core.bot.Config')
    @patch('bot_discord.core.bot.commands.Bot')
    @patch('bot_discord.modules.memory.Memory')
    @patch('bot_discord.modules.ai_handler.AIHandler')
    @patch('bot_discord.modules.search.SearchEngine')
    async def test_personality_change(self, SearchEngineMock, AIHandlerMock, MemoryMock, BotMock, ConfigMock):
        # Arrange
        # Mocking the bot and its modules
        config_instance = ConfigMock.return_value
        config_instance.get_token.return_value = "fake_token"
        config_instance.get_prefix.return_value = "!"
        config_instance.get_config_value.return_value = ""

        bot_instance = DiscordBot()
        bot_instance.bot = BotMock()
        # Mock the bot user
        bot_instance.bot.user = MagicMock()
        bot_instance.bot.user.id = 54321

        memory_instance = MemoryMock()
        ai_handler_instance = AIHandlerMock()
        ai_handler_instance.generate_response = AsyncMock()

        bot_instance._modules['memory'] = memory_instance
        bot_instance._modules['ai_handler'] = ai_handler_instance
        bot_instance._modules['search_engine'] = SearchEngineMock()

        # Mocking the message and context
        message = AsyncMock()
        message.author = MagicMock()
        message.author.id = 12345
        message.author.name = "test_user"
        message.content = "hello bot"
        message.mentions = [bot_instance.bot.user]

        personality = "You are a pirate."

        # Mock the return value for get_permanent_info
        memory_instance.get_permanent_info.return_value = personality

        # Act
        await bot_instance._handle_message_response(message)

        # Assert
        # Check if the AI handler's format_prompt method was called with the correct personality
        ai_handler_instance.format_prompt.assert_called_with(message.content.replace(f'<@{bot_instance.bot.user.id}>', '').strip(), personality)

if __name__ == '__main__':
    unittest.main()
