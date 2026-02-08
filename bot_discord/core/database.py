# database.py
# Gerenciamento assíncrono do banco de dados SQLite

import aiosqlite
import logging
import os
import json
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path=None):
        self.db_path = db_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data',
            'bot_database.db'
        )
        self._db = None

    async def connect(self):
        """Estabelece conexão com o banco de dados e cria tabelas se necessário."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self._db = await aiosqlite.connect(self.db_path)
            self._db.row_factory = aiosqlite.Row
            await self._create_tables()
            logger.info(f"Conectado ao banco de dados: {self.db_path}")
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            raise

    async def _create_tables(self):
        """Cria a estrutura de tabelas inicial com índices para performance."""
        queries = [
            "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT, blob_value BLOB)",
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                affinity REAL DEFAULT 0.0,
                mood TEXT DEFAULT 'neutral',
                interactions INTEGER DEFAULT 0,
                interruption_count INTEGER DEFAULT 0,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}'
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_users_last_seen ON users(last_seen)",
            # Summaries (Long-term Journal)
            """
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                content TEXT NOT NULL,
                embedding BLOB,
                importance INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id)",
            """
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                role TEXT CHECK(role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_history_user_time ON conversation_history(user_id, timestamp)",
            
            # Tabela de Perfis de Personagem
            """
            CREATE TABLE IF NOT EXISTS character_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                is_active INTEGER DEFAULT 0,
                identity_json TEXT,
                personality_json TEXT,
                history_json TEXT,
                emotions_json TEXT,
                social_json TEXT,
                interaction_json TEXT,
                technical_json TEXT,
                voice_dna BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        for query in queries:
            await self._db.execute(query)
        await self._db.commit()

    async def close(self):
        if self._db:
            await self._db.close()
            logger.info("Conexão com banco de dados fechada.")

    async def get_setting(self, key, default=None, return_blob=False):
        async with self._db.execute("SELECT value, blob_value FROM settings WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[1] if return_blob else row[0]
            return default

    async def set_setting(self, key, value, blob_value=None):
        await self._db.execute(
            "INSERT OR REPLACE INTO settings (key, value, blob_value) VALUES (?, ?, ?)", 
            (key, str(value) if value is not None else None, blob_value)
        )
        await self._db.commit()

    async def increment_interruptions(self, user_id):
        """Incrementa o contador de vezes que este usuário interrompeu o bot."""
        await self._db.execute(
            "UPDATE users SET interruption_count = interruption_count + 1 WHERE user_id = ?", 
            (str(user_id),)
        )
        await self._db.commit()

    async def update_user_interaction(self, user_id, username):
        now = datetime.now().isoformat()
        await self._db.execute(f"""
            INSERT INTO users (user_id, username, last_seen, interactions)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                last_seen = excluded.last_seen,
                interactions = interactions + 1
        """, (str(user_id), username, now))
        await self._db.commit()

    async def get_user(self, user_id):
        async with self._db.execute("SELECT * FROM users WHERE user_id = ?", (str(user_id),)) as cursor:
            return await cursor.fetchone()

    async def update_affinity(self, user_id, change):
        await self._db.execute("UPDATE users SET affinity = affinity + ? WHERE user_id = ?", (change, str(user_id)))
        await self._db.commit()

    async def update_mood(self, user_id, mood):
        """Atualiza o estado emocional do usuario."""
        await self._db.execute("UPDATE users SET mood = ? WHERE user_id = ?", (mood, str(user_id)))
        await self._db.commit()

    async def add_summary(self, user_id, content):
        """Adiciona um resumo de conversa ao jornal de longo prazo."""
        await self._db.execute("INSERT INTO summaries (user_id, content) VALUES (?, ?)", (str(user_id), content))
        await self._db.commit()

    async def get_summaries(self, user_id, limit=3):
        """Recupera os ultimos resumos do jornal."""
        async with self._db.execute(
            "SELECT content FROM summaries WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (str(user_id), limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]

    async def add_history(self, user_id, role, content):
        await self._db.execute("INSERT INTO conversation_history (user_id, role, content) VALUES (?, ?, ?)", (str(user_id), role, content))
        await self._db.commit()

    async def get_history(self, user_id, limit=20):
        async with self._db.execute(
            "SELECT role, content FROM conversation_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (str(user_id), limit)
        ) as cursor:
            rows = await cursor.fetchall()
            return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    async def add_memory(self, user_id, content, importance=1, embedding=None):
        blob = embedding.tobytes() if embedding is not None else None
        await self._db.execute("INSERT INTO memories (user_id, content, importance, embedding) VALUES (?, ?, ?, ?)", (str(user_id), content, importance, blob))
        await self._db.commit()

    async def get_semantic_memories(self, user_id, query_embedding, limit=3, threshold=0.7):
        """Busca memórias otimizada usando vetorização Numpy."""
        async with self._db.execute(
            "SELECT content, embedding FROM memories WHERE user_id = ? OR user_id = 'global_legacy'",
            (str(user_id),)
        ) as cursor:
            rows = await cursor.fetchall()
        
        if not rows: return []

        contents = [r[0] for r in rows if r[1] is not None]
        embeddings = [np.frombuffer(r[1], dtype=np.float32) for r in rows if r[1] is not None]
        
        if not embeddings: return []

        matrix = np.vstack(embeddings)
        norm_matrix = np.linalg.norm(matrix, axis=1)
        norm_query = np.linalg.norm(query_embedding)
        
        scores = np.dot(matrix, query_embedding) / (norm_matrix * norm_query + 1e-9)
        
        results = [(contents[i], float(scores[i])) for i in range(len(scores)) if scores[i] >= threshold]
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    async def clear_history(self, user_id):
        await self._db.execute("DELETE FROM conversation_history WHERE user_id = ?", (str(user_id),))
        await self._db.commit()