import asyncio
from unittest.mock import AsyncMock, MagicMock

from bot_discord.modules.setup import CharacterWizard


def test_save_profile_persists_data():
    async def run_test():
        db = MagicMock()
        db._db.execute = AsyncMock()
        db._db.commit = AsyncMock()
        wizard = CharacterWizard(MagicMock(), db, MagicMock(), MagicMock(), MagicMock())
        payload = {
            "identity": {"name": "Teste"},
            "personality": {"traits": "calmo"},
            "history": {"backstory": "origem"},
            "emotions": {"sensitivity": "alta"},
            "social": {"role": "amigo"},
            "interaction": {"style": "direto"},
            "technical": {"temperature": 0.7},
        }

        await wizard.save_profile(payload, voice_dna_blob=b"voice")
        db._db.execute.assert_awaited()
        db._db.commit.assert_awaited_once()

    asyncio.run(run_test())
