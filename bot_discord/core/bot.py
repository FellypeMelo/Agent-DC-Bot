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
from modules.memory import Memory
from modules.ai_handler import AIHandler
from modules.commands import CommandHandler

# Configuração do logger
logger = setup_logger(__name__)

class DiscordBot:
    def __init__(self):
        self.config = Config()
        self.token = self.config.get_token()
        
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        self.bot = commands.Bot(command_prefix=self.config.get_prefix(), intents=intents)
        
        # Inicializa os módulos na ordem correta de dependência
        self.memory = Memory(self.config)
        self.db = self.memory.db  # Acessa a instância do DB a partir da memória
        self.ai_handler = AIHandler(self.config, self.db)
        self.command_handler = CommandHandler(self.bot, self.config, self.memory, self.ai_handler, self.db)

        self.interaction_counter = 0
        self.summary_threshold = 10
        
        self.register_events()
        
    def register_events(self):
        @self.bot.event
        async def on_ready():
            logger.info(f'Bot conectado como {self.bot.user.name}')

        @self.bot.event
        async def on_message(message):
            if message.author == self.bot.user:
                return
            
            ctx = await self.bot.get_context(message)
            if ctx.valid:
                await self.bot.process_commands(message)
            else:
                await self._handle_message_response(message)
    
    async def _handle_message_response(self, message):
        was_mentioned = self.bot.user in message.mentions
        keyword = self.config.get_config_value('bot_keyword', '')
        contains_keyword = keyword and keyword.lower() in message.content.lower()
        
        if was_mentioned or contains_keyword:
            async with message.channel.typing():
                user_message = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
                
                self.memory.add_message(message.author.id, message.author.name, user_message)

                if self.ai_handler.detect_memory_triggers(user_message, self.memory):
                    await message.add_reaction('💾')

                context = self.memory.get_combined_memory(user_message)

                response = await self.ai_handler.generate_response(user_message, context, user_id=message.author.id)

                self.memory.add_message(self.bot.user.id, self.bot.user.name, response, is_bot=True)

                await message.channel.send(response)

                self.interaction_counter += 1
                if self.interaction_counter >= self.summary_threshold:
                    self.interaction_counter = 0
                    conversation = self.memory.get_recent_messages(limit=self.summary_threshold * 2)
                # Executa a extração de fatos e a análise de relacionamento em paralelo
                await asyncio.gather(
                    self.ai_handler.extract_and_memorize_facts(conversation, self.memory),
                    self.ai_handler.analyze_and_update_relationship(message.author.id, conversation)
                )
    
    def run(self):
        try:
            logger.info("Iniciando o bot...")
            self.bot.run(self.token)
        except Exception as e:
            logger.error(f"Erro ao iniciar o bot: {e}")
            
def start_bot():
    bot = DiscordBot()
    bot.run()
    
if __name__ == "__main__":
    start_bot()
