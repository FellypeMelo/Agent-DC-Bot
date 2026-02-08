# migrate_json_to_sqlite.py
import json
import sqlite3
import os
import sys

def migrate():
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot_discord', 'data')
    config_file = os.path.join(data_dir, 'config.json')
    memory_file = os.path.join(data_dir, 'memory.json')
    db_file = os.path.join(data_dir, 'bot_database.db')

    if not os.path.exists(db_file):
        print("Erro: Banco de dados não inicializado. Execute o bot uma vez ou crie o DB.")
        # Como o bot ainda não rodou com o novo código, vamos criar o DB aqui se necessário
        
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Cria tabelas se não existirem (fallback)
    cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, username TEXT, affinity REAL DEFAULT 0.0, interactions INTEGER DEFAULT 0, first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP, metadata TEXT DEFAULT '{}')")
    cursor.execute("CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, content TEXT NOT NULL, embedding BLOB, importance INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    
    # Migrar Config
    if os.path.exists(config_file):
        print(f"Migrando {config_file}...")
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            for key, value in config.items():
                cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    
    # Migrar Memória
    if os.path.exists(memory_file):
        print(f"Migrando {memory_file}...")
        with open(memory_file, 'r', encoding='utf-8') as f:
            memory_data = json.load(f)
            
            # Migrar Memória de Longo Prazo
            long_term = memory_data.get('long_term', {})
            for key, data in long_term.items():
                # No formato antigo era um dict {value, timestamp}
                value = data.get('value', '')
                # Tenta associar a um usuário 'system' ou extrair se possível. 
                # Como o sistema antigo era global, vamos usar 'global_legacy'
                cursor.execute("INSERT INTO memories (user_id, content, created_at) VALUES (?, ?, ?)", 
                               ('global_legacy', value, data.get('timestamp')))

    conn.commit()
    conn.close()
    print("Migração concluída com sucesso!")

if __name__ == "__main__":
    migrate()
