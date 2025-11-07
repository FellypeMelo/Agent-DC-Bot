import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import sys
import os

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from bot_discord.modules.commands import CommandHandler

class TestListCustomCommands(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.bot_mock = MagicMock()
        self.config_mock = MagicMock()
        self.memory_mock = MagicMock()
        self.ai_handler_mock = MagicMock()
        self.search_engine_mock = MagicMock()

        # Mock the decorator
        self.bot_mock.command.return_value = lambda x: x

        with patch('bot_discord.modules.setup.SetupWizard'), \
             patch.object(CommandHandler, '_load_custom_commands'):
            self.command_handler = CommandHandler(
                bot=self.bot_mock,
                config=self.config_mock,
                memory=self.memory_mock,
                ai_handler=self.ai_handler_mock,
                search_engine=self.search_engine_mock
            )

    async def test_list_custom_commands_sends_embed_when_commands_exist(self):
        # Arrange
        self.command_handler.custom_commands = {"test": {"response": "test response"}}
        self.config_mock.get_prefix.return_value = "!"
        ctx = AsyncMock()

        # Act
        await self.command_handler._list_custom_commands(ctx)

        # Assert
        ctx.send.assert_called_once()
        self.assertIn("embed", ctx.send.call_args.kwargs)

    async def test_list_custom_commands_sends_message_when_no_commands_exist(self):
        # Arrange
        self.command_handler.custom_commands = {}
        ctx = AsyncMock()

        # Act
        await self.command_handler._list_custom_commands(ctx)

        # Assert
        ctx.send.assert_called_once_with("ℹ️ Não há comandos personalizados registrados.")

if __name__ == '__main__':
    unittest.main()
