import asyncio
from unittest.mock import AsyncMock, MagicMock

import numpy as np

from bot_discord.modules.memory import Memory


def test_add_message_updates_affinity_and_mood():
    async def run_test():
        db = MagicMock()
        db.add_history = AsyncMock()
        db.update_affinity = AsyncMock()
        db.update_mood = AsyncMock()
        config = MagicMock()
        config.get_memory_limit.return_value = 25
        memory = Memory(config, db)

        await memory.add_message("1", "user", "obrigado por tudo", is_bot=False)
        db.add_history.assert_awaited_once()
        db.update_affinity.assert_awaited_once()
        db.update_mood.assert_awaited_once_with("1", "happy")

    asyncio.run(run_test())


def test_get_context_collects_memories():
    async def run_test():
        db = MagicMock()
        db.get_history = AsyncMock(return_value=[{"role": "user", "content": "hi"}])
        db.get_summaries = AsyncMock(return_value=["resumo"])
        db.get_semantic_memories = AsyncMock(return_value=[("mem", 0.9)])
        config = MagicMock()
        config.get_memory_limit.return_value = 25
        memory = Memory(config, db)
        memory.embeddings.get_embedding = MagicMock(return_value=np.array([1.0], dtype=np.float32))

        context = await memory.get_context("1", query_text="hi")
        assert context["history"]
        assert context["memories"] == ["mem"]
        assert context["journal"] == ["resumo"]

    asyncio.run(run_test())
