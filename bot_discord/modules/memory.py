# bot_discord/modules/memory.py
# Sistema de memória com banco de dados SQLite e busca semântica

import logging
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from database import Database

# Configuração do logger
logger = logging.getLogger(__name__)

class Memory:
    def __init__(self, config):
        self.config = config
        self.memory_limit = config.get_memory_limit()
        
        # Carrega o modelo de sentence transformer
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

        # Caminho para o banco de dados
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data',
            'memory.db'
        )
        
        # Inicializa o banco de dados
        self.db = Database(db_path)

    def add_message(self, user_id, username, message, is_bot=False):
        """Adiciona uma mensagem à memória de curto prazo no banco de dados."""
        return self.db.add_short_term_message(user_id, username, message, is_bot)

    def get_recent_messages(self, limit=None):
        """Retorna as mensagens mais recentes da memória de curto prazo."""
        if limit is None:
            limit = self.memory_limit
        return self.db.get_short_term_messages(limit)

    def clear_short_term(self):
        """Limpa a memória de curto prazo."""
        return self.db.clear_short_term_memory()

    def find_relevant_memories(self, query, top_k=3):
        """Encontra as memórias de longo prazo mais relevantes para uma consulta."""
        if not query:
            return []

        try:
            query_embedding = self.model.encode([query])
            all_memories = self.get_all_permanent_info()

            if not all_memories:
                return []

            memory_embeddings = np.array([np.frombuffer(m['embedding'], dtype=np.float32) for m in all_memories if m['embedding']])

            if memory_embeddings.size == 0:
                return []

            similarities = cosine_similarity(query_embedding, memory_embeddings)[0]
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            return [all_memories[i] for i in top_indices if similarities[i] > 0.5]
        except Exception as e:
            logger.error(f"Erro ao encontrar memórias relevantes: {e}")
            return []

    def get_combined_memory(self, query=None):
        """
        Retorna uma combinação da memória de curto prazo com informações
        relevantes da memória de longo prazo encontradas via busca semântica.
        """
        short_term = self.get_recent_messages()
        
        if not query:
            return short_term

        relevant_long_term = self.find_relevant_memories(query)

        long_term_info = [
            {
                "user_id": "system",
                "username": "system",
                "content": f"Informação relevante: {info['value']}",
                "timestamp": info['timestamp'],
                "is_bot": False,
                "is_memory": True
            } for info in relevant_long_term
        ]
        
        return long_term_info + short_term

    def store_permanent_info(self, key, value):
        """
        Armazena uma informação permanente na memória de longo prazo,
        incluindo seu embedding vetorial.
        """
        try:
            embedding = self.model.encode([value])[0]
            return self.db.store_permanent_info(key, value, embedding.tobytes())
        except Exception as e:
            logger.error(f"Erro ao gerar embedding para '{value}': {e}")
            return False

    def get_permanent_info(self, key):
        """Recupera uma informação permanente da memória de longo prazo."""
        return self.db.get_permanent_info(key)

    def get_all_permanent_info(self):
        """Retorna todas as informações da memória de longo prazo."""
        return self.db.get_all_permanent_info()
