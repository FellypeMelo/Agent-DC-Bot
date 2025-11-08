# bot.py
# Inicialização do bot e conexão com Discord

import discord
from discord.ext import commands
import os
import sys
import logging

# Adiciona o diretório raiz ao path para importações relativas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import Config
from core.logger import setup_logger

# Configuração do logger
logger = setup_logger(__name__)

class DiscordBot:
    def __init__(self):
        self.config = Config()
        self.token = self.config.get_token()
        
        # Configuração de intents para o bot
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        # Inicialização do bot com prefixo de comando
        self.bot = commands.Bot(command_prefix=self.config.get_prefix(), intents=intents)
        
        # Módulos do bot (serão inicializados sob demanda)
        self._modules = {}
        
        # Registrar eventos
        self.register_events()
        
    def register_events(self):
        @self.bot.event
        async def on_ready():
            logger.info(f'Bot conectado como {self.bot.user.name}')
            logger.info(f'ID do Bot: {self.bot.user.id}')
            logger.info('------')
            
        @self.bot.event
        async def on_message(message):
            # Ignora mensagens do próprio bot
            if message.author == self.bot.user:
                return
                
            # Processa comandos
            await self.bot.process_commands(message)
            
            # Lógica para responder a menções ou palavras-chave
            await self._handle_message_response(message)
    
    async def _handle_message_response(self, message):
        """Processa mensagens para responder a menções ou palavras-chave"""
        # Verifica se o bot foi mencionado
        was_mentioned = self.bot.user in message.mentions
        
        # Verifica se a mensagem contém a palavra-chave configurada
        keyword = self.config.get_config_value('bot_keyword', '')
        contains_keyword = keyword and keyword.lower() in message.content.lower()
        
        # Se o bot foi mencionado ou a palavra-chave foi detectada
        if was_mentioned or contains_keyword:
            # Inicializa os módulos necessários sob demanda
            if 'memory' not in self._modules:
                from modules.memory import Memory
                self._modules['memory'] = Memory(self.config)
            
            if 'ai_handler' not in self._modules:
                from modules.ai_handler import AIHandler
                self._modules['ai_handler'] = AIHandler(self.config)
            
            if 'search_engine' not in self._modules:
                from modules.search import SearchEngine
                self._modules['search_engine'] = SearchEngine(self.config)
            
            if 'time_handler' not in self._modules:
                from modules.time_handler import TimeHandler
                self._modules['time_handler'] = TimeHandler(self.config)
            
            if 'command_handler' not in self._modules:
                from modules.commands import CommandHandler
                self._modules['command_handler'] = CommandHandler(
                    self.bot,
                    self.config,
                    self._modules['memory'],
                    self._modules['ai_handler'],
                    self._modules['search_engine']
                )
            
            # Adiciona a mensagem à memória
            self._modules['memory'].add_message(message.author.id, message.author.name, message.content)
            
            # Remove a menção do bot da mensagem, se presente
            user_message = message.content
            if was_mentioned:
                user_message = user_message.replace(f'<@{self.bot.user.id}>', '').strip()
                
            # Verifica se a mensagem contém gatilhos para armazenar na memória de longo prazo
            memory_triggered = self._modules['ai_handler'].detect_memory_triggers(user_message, self._modules['memory'])
            if memory_triggered:
                await message.add_reaction('💾')  # Adiciona uma reação para indicar que a informação foi armazenada
            
            # Obtém o contexto da conversa da memória (combinando memória de curto e longo prazo)
            context = self._modules['memory'].get_combined_memory()
            
            # Obtém a personalidade configurada do bot
            bot_personality = self._modules['memory'].get_permanent_info('personality')
            
            # Formata o prompt com a personalidade do bot
            formatted_prompt = self._modules['ai_handler'].format_prompt(user_message, bot_personality)
            
            # Gera a resposta usando o LM Studio (método assíncrono)
            response = await self._modules['ai_handler'].generate_response(
                prompt=user_message,
                personality=bot_personality,
                context=context
            )
            
            # Processa a resposta para melhorar a inteligibilidade
            processed_response = self._modules['ai_handler'].process_response(response)
            
            # Adiciona a resposta do bot à memória
            self._modules['memory'].add_message(self.bot.user.id, self.bot.user.name, processed_response, is_bot=True)
            
            # Envia a resposta
            await message.channel.send(processed_response)
            logger.info(f"Respondeu a uma mensagem de {message.author.name}")
    
    def load_commands(self):
        """Carrega os módulos e comandos do bot"""
        # Inicializa todos os módulos necessários
        if 'memory' not in self._modules:
            from modules.memory import Memory
            self._modules['memory'] = Memory(self.config)
        
        if 'ai_handler' not in self._modules:
            from modules.ai_handler import AIHandler
            self._modules['ai_handler'] = AIHandler(self.config)
        
        if 'search_engine' not in self._modules:
            from modules.search import SearchEngine
            self._modules['search_engine'] = SearchEngine(self.config)
        
        if 'time_handler' not in self._modules:
            from modules.time_handler import TimeHandler
            self._modules['time_handler'] = TimeHandler(self.config)
        
        if 'command_handler' not in self._modules:
            from modules.commands import CommandHandler
            self._modules['command_handler'] = CommandHandler(
                self.bot,
                self.config,
                self._modules['memory'],
                self._modules['ai_handler'],
                self._modules['search_engine']
            )
        
    def run(self):
        try:
            logger.info("Iniciando o bot...")
            self.bot.run(self.token)
        except Exception as e:
            logger.error(f"Erro ao iniciar o bot: {e}")
            
# Função para iniciar o bot
def start_bot():
    bot = DiscordBot()
    bot.load_commands()
    bot.run()
    
if __name__ == "__main__":
    start_bot()