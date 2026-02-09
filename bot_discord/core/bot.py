# bot.py
import discord
from discord.ext import commands
import os
import sys
import logging
import json

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import Config
from core.logger import setup_logger
from core.database import DatabaseManager
from core.voice_engine import VoiceEngine
from core.llama_server import LlamaServerManager

logger = setup_logger(__name__)

class DiscordBot:
    def __init__(self):
        self.db = DatabaseManager()
        self.config = Config(self.db)
        self.voice_engine = VoiceEngine(self.config)
        self.llama_server = LlamaServerManager(self.config)
        self.bot = None
        self._modules = {}

    def register_events(self):
        @self.bot.event
        async def on_ready():
            if not self.db._db:
                await self.db.connect()
            logger.info(f'--- Bot Online: {self.bot.user.name} (ID: {self.bot.user.id}) ---')
            logger.info(f'Prefixo ativo: {self.bot.command_prefix}')
            
        @self.bot.event
        async def on_message(message):
            if message.author == self.bot.user:
                return
            
            # Processa comandos primeiro
            await self.bot.process_commands(message)
            
            # Lógica de conversação (IA)
            await self._handle_message_response(message)

    async def load_modules(self):
        """Carrega todos os Cogs de forma explícita."""
        try:
            from modules.memory import Memory
            from modules.ai_handler import AIHandler
            from modules.voice_client import VoiceHandler
            from modules.setup import CharacterWizard
            from modules.commands import CommandHandler

            # 0. Start Llama Server if needed
            backend = await self.config.get_config_db("llm_backend", "lm_studio")
            if backend == "llama_cpp":
                logger.info("Configurado para usar llama.cpp. Iniciando servidor...")
                self.llama_server.start()
                if not await self.llama_server.wait_for_ready(timeout=60):
                    logger.error("Falha ao iniciar Llama Server. O bot pode não funcionar corretamente.")

            # 1. Base
            self._modules['memory'] = Memory(self.config, self.db)
            self._modules['ai_handler'] = AIHandler(self.config)
            await self._modules['ai_handler'].initialize()

            # 2. Registrar Cogs no Discord (Pycord add_cog is synchronous)
            self.bot.add_cog(VoiceHandler(self.bot, self.voice_engine))
            self.bot.add_cog(CharacterWizard(self.bot, self.db, self._modules['ai_handler'], self.voice_engine, self._modules['memory']))
            self.bot.add_cog(CommandHandler(self.bot, self.config, self._modules['memory'], self._modules['ai_handler']))
            
            logger.info("Todos os módulos carregados com sucesso.")
        except Exception as e:
            logger.error(f"Erro crítico no carregamento de módulos: {e}", exc_info=True)

    async def _handle_message_response(self, message):
        """Lógica de resposta da IA (Menção ou Keyword)"""
        # Se a mensagem foi um comando (começa com o prefixo), ignoramos a resposta automática de IA
        if message.content.startswith(self.bot.command_prefix):
            return

        was_mentioned = self.bot.user in message.mentions
        keyword = await self.config.get_config_db('bot_keyword', 'blepp')
        contains_keyword = keyword.lower() in message.content.lower()

        if was_mentioned or contains_keyword:
            logger.info(f"IA ativada por {message.author.name} (Mention: {was_mentioned}, Keyword: {contains_keyword})")
            
            # Limpa o texto
            user_message = message.content.replace(f'<@{self.bot.user.id}>', '').replace(f'<@!{self.bot.user.id}>', '').strip()
            
            # Se não houver canal (raro), não podemos mostrar typing mas podemos processar
            typing_ctx = message.channel.typing() if message.channel else None
            
            try:
                if typing_ctx:
                    await typing_ctx.__aenter__()

                # Contexto e Memória
                context_data = await self._modules['memory'].get_context(message.author.id, query_text=user_message)
                base_personality = await self._get_active_profile_prompt()
                
                logger.debug(f"Gerando resposta para: {user_message}")
                # Geração Stream
                response_gen = self._modules['ai_handler'].generate_response_stream(
                    prompt=user_message,
                    personality=base_personality,
                    context=context_data['history']
                )
                
                full_response = ""
                sent_msg = None
                async for chunk in response_gen:
                    full_response += chunk
                    # Só tenta enviar texto se houver um canal real
                    if message.channel:
                        if not sent_msg and len(full_response) > 5:
                            try:
                                sent_msg = await message.channel.send(full_response)
                            except: pass
                        elif sent_msg and len(full_response) % 40 == 0: 
                            try:
                                await sent_msg.edit(content=full_response)
                            except: pass
                
                if not full_response:
                    full_response = "Desculpe, não consegui pensar em nada."

                if sent_msg: 
                    try: await sent_msg.edit(content=full_response)
                    except: pass
                elif message.channel:
                    try: await message.channel.send(full_response)
                    except: pass

                logger.info(f"Resposta gerada ({len(full_response)} chars).")

                # Resposta por Voz
                if message.guild and message.guild.voice_client:
                    logger.debug("Encaminhando resposta para VoiceHandler...")
                    voice_cog = self.bot.get_cog("VoiceHandler")
                    if voice_cog:
                        processed_text, sentiment = self._modules['ai_handler'].extract_sentiment(full_response)
                        await voice_cog.speak(processed_text, sentiment=sentiment, vc=message.guild.voice_client)
                    else:
                        logger.warning("VoiceHandler cog não encontrado!")

            except Exception as e:
                logger.error(f"Erro ao processar resposta: {e}", exc_info=True)
            finally:
                if typing_ctx:
                    await typing_ctx.__aexit__(None, None, None)

    async def _get_active_profile_prompt(self):
        try:
            async with self.db._db.execute("SELECT identity_json, personality_json FROM character_profiles WHERE is_active = 1") as cursor:
                row = await cursor.fetchone()
                if row:
                    id_p = json.loads(row[0])
                    pers_p = json.loads(row[1])
                    return f"Você é {id_p.get('name')}. Personalidade: {pers_p.get('traits')}"
            return "Você é um assistente útil."
        except:
            return "Você é um assistente útil."

    def run(self):
        token = self.config.get_token()
        
        async def runner():
            # Initialize Bot inside the loop to avoid "future belongs to different loop" errors
            intents = discord.Intents.default()
            intents.message_content = True
            intents.members = True
            
            prefix = os.getenv('COMMAND_PREFIX', '-')
            self.bot = commands.Bot(command_prefix=prefix, intents=intents, help_command=None)
            self.bot.owner_instance = self
            self.register_events()

            # Connect DB first
            await self.db.connect()
            
            # Load modules
            await self.load_modules()
            
            try:
                logger.info("Tentando conectar ao Discord...")
                await self.bot.start(token)
            except Exception as e:
                logger.error(f"Erro fatal no bot.start: {e}", exc_info=True)
            finally:
                if self.llama_server:
                    self.llama_server.stop()
                if not self.bot.is_closed():
                    await self.bot.close()

        import asyncio
        try:
            asyncio.run(runner())
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    DiscordBot().run()