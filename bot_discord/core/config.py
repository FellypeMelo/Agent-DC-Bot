# config.py
# Configuração de variáveis globais

import json
import os
import logging
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    def __init__(self, config_path=None):
        self.logger = logging.getLogger(__name__)
        
        # Caminho para o arquivo de configuração
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data',
            'config.json'
        )
        
        # Configurações padrão
        self.default_config = {
            "prefix": "!",
            "memory_limit": 25,
            "memory_persistence": True,
            "ai_model": "default",
            "search_enabled": False,
            "log_level": "INFO",
            "bot_keyword": "",
            "active_personality_name": "default", # Nome da personalidade ativa
            "bot_personality": "assistente amigável", # Descrição da personalidade padrão
            "timezone_offset": -3,
            "locale": "pt_BR",
            "time_awareness": True,
            "moderation_enabled": False,
            "notifications_enabled": False
        }
        
        # Carrega ou cria configurações
        self.config = self.load_config()
        
    def load_config(self):
        """Carrega configurações do arquivo ou cria um novo se não existir"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Cria o diretório se não existir
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                
                # Cria o arquivo de configuração com valores padrão
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.default_config, f, indent=4)
                    
                return self.default_config
        except Exception as e:
            self.logger.error(f"Erro ao carregar configurações: {e}")
            return self.default_config
    
    def save_config(self):
        """Salva as configurações atuais no arquivo"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar configurações: {e}")
            return False
    
    def get_token(self):
        """Obtém o token do Discord das variáveis de ambiente"""
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            self.logger.error("Token do Discord não encontrado nas variáveis de ambiente")
        return token
    
    def get_prefix(self):
        """Obtém o prefixo de comando atual"""
        return self.config.get("prefix", self.default_config["prefix"])
    
    def set_prefix(self, prefix):
        """Define um novo prefixo de comando"""
        self.config["prefix"] = prefix
        return self.save_config()
    
    def get_memory_limit(self):
        """Obtém o limite de memória atual"""
        return self.config.get("memory_limit", self.default_config["memory_limit"])
    
    def set_memory_limit(self, limit):
        """Define um novo limite de memória"""
        self.config["memory_limit"] = limit
        return self.save_config()
    
    def get_config_value(self, key, default=None):
        """Obtém um valor de configuração específico"""
        return self.config.get(key, default or self.default_config.get(key))
    
    def set_config_value(self, key, value):
        """Define um valor de configuração específico"""
        self.config[key] = value
        return self.save_config()