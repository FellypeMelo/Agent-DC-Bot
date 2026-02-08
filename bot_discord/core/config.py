# config.py
# Configuração de variáveis globais

import json
import os
import logging
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    def __init__(self, db=None):
        self.logger = logging.getLogger(__name__)
        self.db = db
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Configurações padrão
        self.default_config = {
            "prefix": os.getenv('BOT_PREFIX', '!'),
            "memory_limit": 25,
            "memory_persistence": True,
            "ai_model": "llama-3",
            "use_ollama": os.getenv('USE_OLLAMA', 'false').lower() == 'true',
            "lm_studio_api_url": os.getenv('LM_STUDIO_API_URL', 'http://localhost:1234/v1'),
            "ollama_api_url": os.getenv('OLLAMA_API_URL', 'http://localhost:11434/v1'),
            "ollama_model": os.getenv('OLLAMA_MODEL', 'ministral-3:3b'),
            "model_path": os.getenv('LLM_MODEL_PATH', os.path.join(self.base_path, "data", "models", "model.gguf")),
            "device": os.getenv('DEVICE', 'xpu'),
            "search_enabled": False,
            "log_level": "INFO",
            "bot_keyword": "bro",
            "bot_personality": "casual e amigável",
            "moderation_enabled": False,
        }
        
    def get_token(self):
        """Obtém o token do Discord das variáveis de ambiente"""
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            self.logger.error("Token do Discord não encontrado nas variáveis de ambiente")
        return token
    
    def get_prefix(self):
        # Como o bot.py precisa do prefixo ANTES de conectar o DB para o commands.Bot, 
        # vamos manter o prefixo no .env ou um fallback fixo por enquanto.
        return os.getenv('BOT_PREFIX', '!')
    
    def get_memory_limit(self):
        return 25 # Fallback fixo
    
    def get_config_value(self, key, default=None):
        """Obtém um valor de configuração. Nota: Este método agora deve ser preferencialmente async, 
        mas para manter compatibilidade síncrona onde necessário, usamos fallbacks."""
        return self.default_config.get(key, default)

    async def get_config_db(self, key, default=None):
        """Versão assíncrona que busca no banco de dados."""
        if not self.db:
            return self.get_config_value(key, default)
        val = await self.db.get_setting(key)
        return val if val is not None else self.get_config_value(key, default)

    async def set_config_db(self, key, value):
        """Versão assíncrona que salva no banco de dados."""
        if self.db:
            await self.db.set_setting(key, value)
            return True
        return False