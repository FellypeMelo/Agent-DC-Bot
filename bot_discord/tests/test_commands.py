import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from bot_discord.modules.commands import CommandHandler


class AsyncCursor:
    def __init__(self, rows):
        self._rows = rows

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def fetchall(self):
        return self._rows

    async def fetchone(self):
        return self._rows[0] if self._rows else None


@pytest.fixture()
def command_handler():
    bot = MagicMock()
    bot.command_prefix = "!"
    bot.get_cog.return_value = None
    config = MagicMock()
    memory = MagicMock()
    ai_handler = MagicMock()
    return CommandHandler(bot=bot, config=config, memory=memory, ai_handler=ai_handler)


def test_ajuda_sends_embed(command_handler):
    async def run_test():
        ctx = AsyncMock()
        await command_handler.ajuda.callback(command_handler, ctx)
        ctx.send.assert_called_once()
        _, kwargs = ctx.send.call_args
        assert "embed" in kwargs
        assert kwargs["embed"].fields

    asyncio.run(run_test())


def test_status_includes_tts_state(command_handler):
    async def run_test():
        ctx = AsyncMock()
        voice_engine = SimpleNamespace(kokoro=True, model=None)
        voice_cog = SimpleNamespace(voice_engine=voice_engine)
        command_handler.bot.get_cog.return_value = voice_cog
        await command_handler.status.callback(command_handler, ctx)
        ctx.send.assert_called_once()
        _, kwargs = ctx.send.call_args
        assert "embed" in kwargs

    asyncio.run(run_test())


def test_limpar_clears_history(command_handler):
    async def run_test():
        ctx = AsyncMock()
        ctx.author.id = 123
        command_handler.memory.db.clear_history = AsyncMock()
        await command_handler.limpar.callback(command_handler, ctx)
        command_handler.memory.db.clear_history.assert_awaited_once_with(123)
        ctx.send.assert_called_once_with("🧹 Histórico de conversa limpo!")

    asyncio.run(run_test())


def test_memorias_lists_rows(command_handler):
    async def run_test():
        ctx = AsyncMock()
        ctx.author.id = 55
        rows = [("memoria 1",), ("memoria 2",)]
        db = SimpleNamespace()
        db.execute = MagicMock(return_value=AsyncCursor(rows))
        command_handler.memory.db._db = db

        await command_handler.memorias.callback(command_handler, ctx)
        ctx.send.assert_called_once()
        sent_text = ctx.send.call_args.args[0]
        assert "memoria 1" in sent_text
        assert "memoria 2" in sent_text

    asyncio.run(run_test())


def test_perfil_returns_active_profile(command_handler):
    async def run_test():
        ctx = AsyncMock()
        profile = {"name": "Blepp"}
        rows = [(json.dumps(profile),)]
        db = SimpleNamespace()
        db.execute = MagicMock(return_value=AsyncCursor(rows))
        command_handler.memory.db._db = db

        await command_handler.perfil.callback(command_handler, ctx)
        ctx.send.assert_called_once_with("👤 **Perfil Ativo:** Blepp")

    asyncio.run(run_test())
