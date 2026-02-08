import asyncio
from unittest.mock import AsyncMock

from bot_discord.core.config import Config


def test_get_prefix_from_env(monkeypatch):
    monkeypatch.setenv("BOT_PREFIX", "?")
    config = Config()
    assert config.get_prefix() == "?"


def test_get_config_db_falls_back_to_default():
    config = Config()
    assert config.get_config_value("bot_keyword") == "bro"


def test_get_config_db_reads_from_db():
    async def run_test():
        db = AsyncMock()
        db.get_setting.return_value = "custom"
        config = Config(db=db)

        value = await config.get_config_db("bot_keyword", "fallback")
        assert value == "custom"

    asyncio.run(run_test())
