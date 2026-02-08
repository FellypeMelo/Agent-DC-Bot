# embeddings.py
import logging
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class EmbeddingManager:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        if self._model is None:
            try:
                logger.info(f"Carregando modelo de embeddings (Lazy): {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.error(f"Erro ao carregar modelo de embeddings: {e}")
        return self._model

    def get_embedding(self, text):
        """Gera um vetor para o texto fornecido."""
        if not self.model:
            return None
        return self.model.encode(text)

    @staticmethod
    def cosine_similarity(v1, v2):
        """Calcula a similaridade de cosseno entre dois vetores."""
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        return dot_product / (norm_v1 * norm_v2)
