# bot_discord/database.py
# Módulo de gerenciamento de banco de dados SQLite

import sqlite3
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self._connect()
        self.create_tables()

    def _connect(self):
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            logger.info("Conexão com o banco de dados SQLite estabelecida.")
        except sqlite3.Error as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            raise

    def create_tables(self):
        try:
            with self.conn:
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS short_term_memory (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        username TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        is_bot BOOLEAN NOT NULL
                    )
                """)
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS long_term_memory (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT UNIQUE NOT NULL,
                        value TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        embedding BLOB
                    )
                """)
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS personalities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        description TEXT NOT NULL,
                        core_memory TEXT,
                        creator_id TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                """)
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_relationships (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT UNIQUE NOT NULL,
                        relationship_status TEXT NOT NULL DEFAULT 'Desconhecido'
                    )
                """)
            logger.info("Tabelas do banco de dados verificadas/criadas.")
        except sqlite3.Error as e:
            logger.error(f"Erro ao criar tabelas: {e}")

    # --- Métodos de Memória ---
    def add_short_term_message(self, user_id, username, message, is_bot=False):
        try:
            with self.conn:
                self.conn.execute(
                    "INSERT INTO short_term_memory (user_id, username, content, timestamp, is_bot) VALUES (?, ?, ?, ?, ?)",
                    (str(user_id), username, message, datetime.now().isoformat(), is_bot)
                )
            return True
        except sqlite3.Error as e:
            logger.error(f"Erro ao adicionar mensagem de curto prazo: {e}")
            return False

    def get_short_term_messages(self, limit=10):
        try:
            with self.conn:
                cursor = self.conn.execute("SELECT user_id, username, content, timestamp, is_bot FROM short_term_memory ORDER BY id DESC LIMIT ?", (limit,))
                return [dict(row) for row in reversed(cursor.fetchall())]
        except sqlite3.Error as e:
            logger.error(f"Erro ao obter mensagens de curto prazo: {e}")
            return []

    def clear_short_term_memory(self):
        try:
            with self.conn:
                self.conn.execute("DELETE FROM short_term_memory")
            return True
        except sqlite3.Error as e:
            logger.error(f"Erro ao limpar a memória de curto prazo: {e}")
            return False

    def store_permanent_info(self, key, value, embedding=None):
        try:
            with self.conn:
                self.conn.execute(
                    "INSERT OR REPLACE INTO long_term_memory (key, value, timestamp, embedding) VALUES (?, ?, ?, ?)",
                    (key, value, datetime.now().isoformat(), embedding)
                )
            return True
        except sqlite3.Error as e:
            logger.error(f"Erro ao armazenar informação permanente: {e}")
            return False

    def get_all_permanent_info(self):
        try:
            with self.conn:
                cursor = self.conn.execute("SELECT key, value, timestamp, embedding FROM long_term_memory")
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Erro ao obter todas as informações permanentes: {e}")
            return []

    # --- Métodos de Personalidade ---
    def create_personality(self, name, description, core_memory, creator_id):
        try:
            with self.conn:
                self.conn.execute(
                    "INSERT INTO personalities (name, description, core_memory, creator_id, created_at) VALUES (?, ?, ?, ?, ?)",
                    (name, description, core_memory, str(creator_id), datetime.now().isoformat())
                )
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Tentativa de criar personalidade com nome duplicado: {name}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Erro ao criar personalidade: {e}")
            return False

    def get_personality(self, name):
        try:
            with self.conn:
                cursor = self.conn.execute("SELECT * FROM personalities WHERE name = ?", (name,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Erro ao obter personalidade: {e}")
            return None

    def get_all_personalities(self):
        try:
            with self.conn:
                cursor = self.conn.execute("SELECT name, description FROM personalities")
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Erro ao obter todas as personalidades: {e}")
            return []

    def delete_personality(self, name):
        try:
            with self.conn:
                cursor = self.conn.execute("DELETE FROM personalities WHERE name = ?", (name,))
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Erro ao deletar personalidade: {e}")
            return False

    # --- Métodos de Relacionamento ---
    def get_relationship(self, user_id):
        try:
            with self.conn:
                cursor = self.conn.execute("SELECT relationship_status FROM user_relationships WHERE user_id = ?", (str(user_id),))
                result = cursor.fetchone()
                return result['relationship_status'] if result else 'Desconhecido'
        except sqlite3.Error as e:
            logger.error(f"Erro ao obter relacionamento: {e}")
            return 'Desconhecido'

    def update_relationship(self, user_id, status):
        try:
            with self.conn:
                self.conn.execute(
                    "INSERT INTO user_relationships (user_id, relationship_status) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET relationship_status = excluded.relationship_status",
                    (str(user_id), status)
                )
            return True
        except sqlite3.Error as e:
            logger.error(f"Erro ao atualizar relacionamento: {e}")
            return False

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Conexão com o banco de dados fechada.")
