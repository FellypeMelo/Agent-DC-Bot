import numpy as np

from bot_discord.core.embeddings import EmbeddingManager


def test_cosine_similarity_handles_zero_norm():
    v1 = np.array([0.0, 0.0], dtype=np.float32)
    v2 = np.array([1.0, 0.0], dtype=np.float32)
    assert EmbeddingManager.cosine_similarity(v1, v2) == 0.0


def test_get_embedding_uses_loaded_model():
    manager = EmbeddingManager()

    class FakeModel:
        def encode(self, text):
            return np.array([1.0, 2.0], dtype=np.float32)

    manager._model = FakeModel()
    result = manager.get_embedding("teste")
    assert result.tolist() == [1.0, 2.0]
