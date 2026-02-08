import asyncio
import numpy as np

from bot_discord.core.database import DatabaseManager


def test_database_settings_and_history(tmp_path):
    async def run_test():
        db_path = tmp_path / "test.db"
        manager = DatabaseManager(db_path=str(db_path))
        await manager.connect()

        await manager.set_setting("bot_keyword", "blepp")
        assert await manager.get_setting("bot_keyword") == "blepp"

        await manager.add_history("user1", "user", "hello")
        history = await manager.get_history("user1", limit=5)
        assert history[-1]["content"] == "hello"

        await manager.close()

    asyncio.run(run_test())


def test_database_semantic_memories(tmp_path):
    async def run_test():
        db_path = tmp_path / "test.db"
        manager = DatabaseManager(db_path=str(db_path))
        await manager.connect()

        embedding = np.array([1.0, 0.0], dtype=np.float32)
        await manager.add_memory("user1", "gosta de pizza", embedding=embedding)

        results = await manager.get_semantic_memories("user1", embedding, limit=1, threshold=0.1)
        assert results
        assert results[0][0] == "gosta de pizza"

        await manager.close()

    asyncio.run(run_test())
