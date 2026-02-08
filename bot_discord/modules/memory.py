# memory.py
# Sistema de memória e persistência

import os
import logging
from datetime import datetime
from core.embeddings import EmbeddingManager

# Configuração do logger
logger = logging.getLogger(__name__)

class Memory:
    def __init__(self, config, db):
        self.config = config
        self.db = db
        self.memory_limit = config.get_memory_limit()
        self.embeddings = EmbeddingManager()
    
    async def add_message(self, user_id, username, message, is_bot=False):
        """
        Adiciona uma mensagem e processa dinâmica social (afinidade e humor).
        
        Args:
            user_id (str): ID do Discord.
            username (str): Nome legivel.
            message (str): Conteudo.
            is_bot (bool): Flag de origem.
            
        Big(O): O(1) para escrita, O(N) para processamento de humor.
        """
        role = "assistant" if is_bot else "user"
        await self.db.add_history(user_id, role, message)
        
        if not is_bot:
            # Lógica de Afinidade e Humor (KISS)
            change = 0.01 
            positive = ["obrigado", "vlw", "bom", "legal", "amo", "gosto", "feliz", "amigo"]
            negative = ["chato", "odiei", "ruim", "burro", "idiota", "pare", "calado"]
            
            msg_lower = message.lower()
            current_mood = "neutral"
            
            if any(w in msg_lower for w in positive): 
                change += 0.05
                current_mood = "happy"
            if any(w in msg_lower for w in negative): 
                change -= 0.1
                current_mood = "annoyed"
            
            await self.db.update_affinity(user_id, change)
            if current_mood != "neutral":
                await self.db.update_mood(user_id, current_mood)
        
        return True
    
    async def get_context(self, user_id, query_text=None):
        """
        Recupera o contexto completo: Historico + Memorias Semanticas + Resumos.
        
        Big(O): O(M) para busca semantica (vetorizada).
        """
        history = await self.db.get_history(user_id, limit=self.memory_limit)
        summaries = await self.db.get_summaries(user_id, limit=2)
        
        relevant_memories = []
        if query_text:
            query_vec = self.embeddings.get_embedding(query_text)
            if query_vec is not None:
                mems = await self.db.get_semantic_memories(user_id, query_vec)
                relevant_memories = [m[0] for m in mems]
        
        return {
            "history": history,
            "memories": relevant_memories,
            "journal": summaries
        }

    async def process_summarization(self, user_id, ai_handler):
        """
        Verifica se o historico excedeu o limite e cria um resumo (Jornal).
        Limpa o historico antigo para manter performance.
        """
        history = await self.db.get_history(user_id, limit=100)
        if len(history) >= 50:
            logger.info(f"Iniciando sumarizacao para {user_id}...")
            summary = await ai_handler.summarize_history(history)
            await self.db.add_summary(user_id, summary)
            await self.db.clear_history(user_id)
            logger.info("Historico limpo e resumo salvo.")

    async def store_permanent_info(self, user_id, content, importance=1):
        embedding = self.embeddings.get_embedding(content)
        await self.db.add_memory(user_id, content, importance, embedding)
        return True

    async def get_user_stats(self, user_id):
        return await self.db.get_user(user_id)

    async def get_time_gap_context(self, user_id):
        user = await self.db.get_user(user_id)
        if not user or not user['last_seen']: return ""
        try:
            last_seen = datetime.fromisoformat(user['last_seen'])
            delta = datetime.now() - last_seen
            if delta.days > 7: return "Ja faz mais de uma semana que voces nao se falam."
            elif delta.days >= 1: return f"Faz {delta.days} dias que voces nao se falam."
        except: pass
        return ""

    async def clear_long_term(self, user_id):
        await self.db._db.execute("DELETE FROM memories WHERE user_id = ?", (str(user_id),))
        await self.db._db.commit()
