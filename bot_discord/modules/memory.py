# memory.py
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from core.embeddings import EmbeddingManager

logger = logging.getLogger(__name__)

class Memory:
    def __init__(self, config, db):
        """
        Initializes the Memory system for short-term history and long-term semantic storage.
        
        Big (O): O(1) - Constant time initialization.
        """
        self.config = config
        self.db = db
        self.memory_limit = config.get_memory_limit()
        self.embeddings = EmbeddingManager()
        
        # Pre-compiled sets for O(1) average lookup performance in sentiment analysis
        self.POSITIVE_WORDS = {"obrigado", "vlw", "bom", "legal", "amo", "gosto", "feliz", "amigo", "curti"}
        self.NEGATIVE_WORDS = {"chato", "odiei", "ruim", "burro", "idiota", "pare", "calado", "horrível"}
    
    async def add_message(self, user_id: str, username: str, message: str, is_bot: bool = False) -> bool:
        """
        Saves a message to history and updates social dynamics (affinity/mood).
        
        Args:
            user_id: Discord User ID.
            username: Display name.
            message: Text content.
            is_bot: If the sender is the assistant.
            
        Returns:
            Success boolean.
            
        Big (O): O(W) - W is the number of words in the message. 
                Using set intersection for sentiment check is highly efficient.
        """
        role = "assistant" if is_bot else "user"
        
        # 1. Direct I/O: Add to history
        await self.db.add_history(user_id, role, message)
        
        if not is_bot:
            # 2. Update metadata (Parallelizable if needed)
            await self.db.update_user_interaction(user_id, username)
            
            # 3. Optimized Sentiment & Affinity (KISS)
            msg_words = set(message.lower().split())
            change = 0.01 
            current_mood = "neutral"
            
            # Set intersection is O(min(len(msg_words), len(SENTIMENT_WORDS)))
            if msg_words & self.POSITIVE_WORDS:
                change += 0.05
                current_mood = "happy"
            elif msg_words & self.NEGATIVE_WORDS:
                change -= 0.1
                current_mood = "annoyed"
            
            await self.db.update_affinity(user_id, change)
            if current_mood != "neutral":
                await self.db.update_mood(user_id, current_mood)
        
        return True
    
    async def get_context(self, user_id: str, query_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves complete context: History + RAG Memories + Journal Summaries.
        
        Args:
            user_id: Discord User ID.
            query_text: The current user message to use for semantic search.
            
        Returns:
            Context dictionary for the LLM.
            
        Big (O): O(H + S + (M * D)) - H: history size, S: summaries, M: total memories, D: vector dimensions.
                Semantic search is vectorized via Numpy in the database layer.
        """
        # Fetch history and summaries in parallel
        import asyncio
        history_task = self.db.get_history(user_id, limit=self.memory_limit)
        summaries_task = self.db.get_summaries(user_id, limit=2)
        
        history, summaries = await asyncio.gather(history_task, summaries_task)
        
        relevant_memories = []
        if query_text:
            # Embedding generation is the bottleneck here
            query_vec = self.embeddings.get_embedding(query_text)
            if query_vec is not None:
                # Semantic retrieval using cosine similarity
                mems = await self.db.get_semantic_memories(user_id, query_vec)
                relevant_memories = [m[0] for m in mems]
        
        return {
            "history": history,
            "memories": relevant_memories,
            "journal": summaries
        }

    async def process_summarization(self, user_id: str, ai_handler: Any) -> None:
        """
        Maintenance task: Summarizes long histories into the journal to prevent performance degradation.
        
        Big (O): O(H + LLM_Inference) - H is the history length being processed.
        """
        history = await self.db.get_history(user_id, limit=100)
        if len(history) >= 50:
            logger.info(f"Summarizing history for {user_id} (Limit reached).")
            summary = await ai_handler.summarize_history(history)
            
            # Atomic update: Add summary and clear old history
            await self.db.add_summary(user_id, summary)
            await self.db.clear_history(user_id)
            logger.debug("History summarized and cleared.")

    async def store_permanent_info(self, user_id: str, content: str, importance: int = 1) -> bool:
        """
        Stores a fact in long-term vector memory.
        
        Big (O): O(Embed) - Dominant cost is the model encoding.
        """
        embedding = self.embeddings.get_embedding(content)
        await self.db.add_memory(user_id, content, importance, embedding)
        return True

    async def get_time_gap_context(self, user_id: str) -> str:
        """
        Calculates how long since the last interaction to provide temporal awareness.
        
        Big (O): O(1) - Single DB lookup and date subtraction.
        """
        user = await self.db.get_user(user_id)
        if not user or not user['last_seen']: return ""
        
        try:
            last_seen = datetime.fromisoformat(user['last_seen'])
            delta = datetime.now() - last_seen
            if delta.days > 7: 
                return "Já faz mais de uma semana que vocês não se falam."
            elif delta.days >= 1: 
                return f"Faz {delta.days} dias que vocês não se falam."
        except Exception: 
            pass
        return ""