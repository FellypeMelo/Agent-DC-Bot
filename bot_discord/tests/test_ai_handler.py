import asyncio
from unittest.mock import AsyncMock, MagicMock

from bot_discord.modules.ai_handler import AIHandler


def test_trim_context_keeps_system_and_last_messages():
    handler = AIHandler(config=MagicMock())
    messages = [{"role": "system", "content": "sys"}] + [
        {"role": "user", "content": f"msg{i}"} for i in range(20)
    ]
    trimmed = handler._trim_context(messages, max_tokens=12000)
    assert trimmed[0]["role"] == "system"
    assert len(trimmed) <= 15


def test_detect_memory_triggers_adds_memory():
    async def run_test():
        handler = AIHandler(config=MagicMock())
        handler.provider.generate = AsyncMock(return_value='["Gosta de café"]')
        memory_module = MagicMock()
        memory_module.add_memory = AsyncMock()

        triggered = await handler.detect_memory_triggers("Eu gosto de café", memory_module, "123")
        assert triggered is True
        memory_module.add_memory.assert_awaited_once_with("123", "Gosta de café")

    asyncio.run(run_test())


def test_extract_sentiment():
    handler = AIHandler(config=MagicMock())
    text, sentiment = handler.extract_sentiment("Olá [HAPPY]")
    assert sentiment == "happy"
    assert text == "Olá"
