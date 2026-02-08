import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from bot_discord.core.bot import DiscordBot


class AsyncCursor:
    def __init__(self, row):
        self._row = row

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def fetchone(self):
        return self._row


def test_get_active_profile_prompt_returns_profile():
    async def run_test():
        bot = DiscordBot()
        identity = {"name": "Blepp"}
        personality = {"traits": "amigável"}
        row = (json.dumps(identity), json.dumps(personality))
        db = SimpleNamespace()
        db.execute = MagicMock(return_value=AsyncCursor(row))
        bot.db._db = db

        result = await bot._get_active_profile_prompt()
        assert "Blepp" in result
        assert "amigável" in result

    asyncio.run(run_test())


def test_get_active_profile_prompt_returns_default_on_empty():
    async def run_test():
        bot = DiscordBot()
        db = SimpleNamespace()
        db.execute = MagicMock(return_value=AsyncCursor(None))
        bot.db._db = db

        result = await bot._get_active_profile_prompt()
        assert result == "Você é um assistente útil."

    asyncio.run(run_test())
