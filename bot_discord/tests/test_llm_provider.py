import asyncio
from unittest.mock import AsyncMock, MagicMock

from bot_discord.core.llm_provider import LMStudioProvider


class DummyResponse:
    def __init__(self, status, payload=None, text=""):
        self.status = status
        self._payload = payload or {}
        self._text = text

    async def json(self):
        return self._payload

    async def text(self):
        return self._text

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


def test_generate_handles_success(monkeypatch):
    async def run_test():
        provider = LMStudioProvider("http://localhost:1234/v1", "model")
        response = DummyResponse(
            200,
            payload={"choices": [{"message": {"content": "ok"}}]},
        )
        session = MagicMock()
        session.post.return_value = response
        monkeypatch.setattr(provider, "_get_session", AsyncMock(return_value=session))

        result = await provider.generate([{"role": "user", "content": "hi"}])
        assert result == "ok"

    asyncio.run(run_test())


def test_generate_handles_error(monkeypatch):
    async def run_test():
        provider = LMStudioProvider("http://localhost:1234/v1", "model")
        response = DummyResponse(500, text="server error")
        session = MagicMock()
        session.post.return_value = response
        monkeypatch.setattr(provider, "_get_session", AsyncMock(return_value=session))

        result = await provider.generate([{"role": "user", "content": "hi"}])
        assert "Erro no servidor" in result

    asyncio.run(run_test())
