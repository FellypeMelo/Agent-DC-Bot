# voice_client.py
import discord
import asyncio
import io
import numpy as np
import time
from discord.ext import commands
from core.logger import setup_logger

logger = setup_logger("modules.voice_client")

class RealTimeWhisperSink(discord.sinks.Sink):
    """
    Sink customizado para Pycord que processa áudio em tempo real.
    Ele detecta fala via VAD e transcreve via Whisper.
    """
    def __init__(self, voice_handler):
        super().__init__()
        self.handler = voice_handler
        self.user_buffers = {} # userId -> list of audio chunks
        self.user_last_speech = {} # userId -> timestamp
        self.SILENCE_TIMEOUT = 1.2 # Segundos de silêncio para processar a frase
        self.VAD_WINDOW_SIZE = 1024 # Increased window size for lower overhead (approx 64ms)
        
        # Buffer interno para VAD (16k mono)
        self.vad_buffers = {} # userId -> bytearray
        
        # Watchdog para silêncio (Discord para de enviar pacotes quando ninguém fala)
        self.watchdog_task = asyncio.run_coroutine_threadsafe(
            self.silence_watchdog(), 
            self.handler.bot.loop
        )

    async def silence_watchdog(self):
        """Task que roda no loop do bot monitorando silêncio mesmo sem pacotes novos."""
        while True:
            await asyncio.sleep(0.5)
            now = time.time()
            for user_id, last_time in list(self.user_last_speech.items()):
                if self.user_buffers.get(user_id) and (now - last_time > self.SILENCE_TIMEOUT):
                    # Trigger processing
                    audio_to_process = np.concatenate(self.user_buffers[user_id])
                    self.user_buffers[user_id] = []
                    
                    guild = self.handler.bot.voice_clients[0].guild if self.handler.bot.voice_clients else None
                    user = guild.get_member(user_id) if guild else None
                    
                    if user:
                        logger.info(f"Fim de fala detectado para {user.name} (Watchdog). Processando...")
                        asyncio.run_coroutine_threadsafe(
                            self.handler.process_user_speech(user, audio_to_process),
                            self.handler.bot.loop
                        )

    def write(self, data, user_id):
        """
        Recebe áudio 48kHz Stereo do Discord.
        """
        if user_id not in self.user_buffers:
            self.user_buffers[user_id] = []
            self.vad_buffers[user_id] = bytearray()
            self.user_last_speech[user_id] = 0

        # 1. Converter para Mono 16k para o VAD e Whisper
        pcm_data = np.frombuffer(data, dtype=np.int16)
        mono_16k = pcm_data[0::6] 
        
        # 2. Alimentar buffer de VAD (Efficient bytearray extension instead of np.concatenate)
        
        # 3. Processar VAD em janelas
        # Window size in bytes = samples * 2 (int16)
        window_bytes = self.VAD_WINDOW_SIZE * 2

        while len(self.vad_buffers[user_id]) >= window_bytes:
            # Extract window bytes
            chunk_bytes = self.vad_buffers[user_id][:window_bytes]
            # Efficient in-place deletion
            del self.vad_buffers[user_id][:window_bytes]

            # Convert only the window to numpy for VAD
            chunk = np.frombuffer(chunk_bytes, dtype=np.int16)
            
            # Ajuste de sensibilidade: threshold 0.6 para evitar ruído de fundo
            if self.handler.voice_engine.vad and self.handler.voice_engine.vad.is_speech(chunk, threshold=0.6):
                if not self.user_buffers[user_id]:
                    logger.debug(f"Usuário {user_id} começou a falar.")
                
                self.user_buffers[user_id].append(chunk)
                self.user_last_speech[user_id] = time.time()
                
                # Interrupção (Barge-In)
                if self.handler.can_be_interrupted():
                    guild = self.handler.bot.voice_clients[0].guild if self.handler.bot.voice_clients else None
                    user = guild.get_member(user_id) if guild else None
                    if user:
                        asyncio.run_coroutine_threadsafe(self.handler.interrupt(user), self.handler.bot.loop)

    def format_audio(self, dest):
        pass

class VoiceHandler(commands.Cog):
    def __init__(self, bot, voice_engine):
        self.bot = bot
        self.voice_engine = voice_engine
        self.is_interrupted = asyncio.Event()
        self._current_gen_task = None
        self.last_audio_start_time = 0
        self.GRACE_PERIOD_DURATION = 0.5
        logger.info("VoiceHandler (Pycord Version) inicializado.")

    def can_be_interrupted(self) -> bool:
        vc = self.bot.voice_clients[0] if self.bot.voice_clients else None
        if not vc: return False
        if not vc.is_playing() and self._current_gen_task is None: return False
        if time.time() - self.last_audio_start_time < self.GRACE_PERIOD_DURATION: return False
        return True

    async def interrupt(self, user):
        vc = self.bot.voice_clients[0] if self.bot.voice_clients else None
        if vc and (vc.is_playing() or self._current_gen_task):
            logger.info(f"!! BARGE-IN !! {user.name} interrompeu o bot.")
            vc.stop()
            self.is_interrupted.set()
            await self.bot.db.increment_interruptions(user.id)
            self.bot.last_interrupter = user.name
            if self._current_gen_task:
                self._current_gen_task.cancel()

    async def process_user_speech(self, user, audio_data):
        """Callback acionado quando o usuário termina de falar."""
        logger.debug(f"Processando fala de {user.name} ({len(audio_data)} samples)...")
        text = await self.voice_engine.transcribe(audio_data)
        if not text or len(text) < 2: 
            logger.debug(f"Transcrição ignorada ou muito curta para {user.name}.")
            return
        
        logger.info(f"Transcrição de {user.name}: '{text}'")
        
        # Simula o recebimento de uma mensagem para disparar a IA
        # Criamos um "Fake Message" para reaproveitar a lógica do bot.py
        # Nota: No futuro, o bot.py pode ser refatorado para aceitar texto direto.
        # Por ora, chamamos o handler de resposta do bot.py se disponível.
        discord_bot_instance = self.bot.owner_instance # Referência para a classe DiscordBot
        if discord_bot_instance:
            # Criamos um contexto fictício ou chamamos a lógica
            # Para manter o KISS, vamos apenas logar e avisar que precisamos linkar
            logger.debug(f"Encaminhando '{text}' para a lógica de IA...")
            
            # Buscamos um canal de texto para responder (o último usado ou o atual do usuário)
            # Simplificação: O bot vai responder no canal de voz se ele for um Stage ou se tiver permissão
            # Mas o ideal é responder onde a interação começou.
            
            # Vamos disparar o evento on_message manualmente ou chamar a função?
            # Melhor chamar a função de processamento de resposta.
            class FakeMessage:
                def __init__(self, author, content, guild, channel, bot):
                    self.author = author
                    self.content = content
                    self.guild = guild
                    self.channel = channel
                    self.mentions = [bot.user]
                    self.author_id = author.id # For logging/memory
            
            # Tentamos achar um canal de texto no mesmo server ou usamos o canal de voz se suportado
            # No Pycord, VoiceChannel pode receber mensagens em alguns contextos, mas TextChannel é mais seguro.
            target_channel = user.voice.channel if user.voice else None
            
            fake_msg = FakeMessage(user, f"<@{self.bot.user.id}> {text}", user.guild, target_channel, self.bot)
            logger.debug(f"Disparando _handle_message_response para {user.name} no canal {target_channel}")
            await discord_bot_instance._handle_message_response(fake_msg)

    async def speak(self, text, sentiment="neutral", vc=None):
        if not vc:
            vc = self.bot.voice_clients[0] if self.bot.voice_clients else None
        if not vc or not vc.is_connected(): 
            logger.warning("Bot não está conectado a um canal de voz para falar.")
            return

        logger.info(f"Iniciando síntese de voz: '{text[:50]}...'")
        self.is_interrupted.clear()
        self._current_gen_task = asyncio.create_task(
            self.voice_engine.generate_speech(text, sentiment=sentiment)
        )
        
        try:
            audio_data = await self._current_gen_task
            if audio_data and not self.is_interrupted.is_set():
                # Pycord PCMAudio espera stream de bytes
                source = discord.PCMAudio(io.BytesIO(audio_data))
                self.last_audio_start_time = time.time()
                logger.debug("Enviando áudio para o Discord...")
                vc.play(source)
                while vc.is_playing() and not self.is_interrupted.is_set():
                    await asyncio.sleep(0.1)
                logger.debug("Reprodução de áudio finalizada.")
            elif not audio_data:
                logger.error("Falha ao gerar dados de áudio.")
        except asyncio.CancelledError:
            logger.info("TTS Cancelado.")
        except Exception as e:
            logger.error(f"Erro no playback: {e}", exc_info=True)
        finally:
            self._current_gen_task = None

    @commands.command(name="join")
    async def join(self, ctx):
        if not ctx.author.voice:
            await ctx.send("❌ Você precisa estar em um canal de voz.")
            return

        channel = ctx.author.voice.channel
        try:
            vc = await channel.connect()
            
            # No Pycord, usamos start_recording com um Sink
            # Mas o nosso Sink processa em TEMPO REAL no método write
            vc.start_recording(
                RealTimeWhisperSink(self),
                self.finished_callback
            )
            
            # Carrega o motor ultra-rápido (Kokoro) para conversa fluída
            await self.voice_engine.load_engine(mode="fast")
            await self.voice_engine.load_stt() # Carrega o Whisper
            
            await ctx.send(f"🔊 Conectado a **{channel.name}**. O modo Conversa em Tempo Real está ATIVO!")
            logger.info(f"Bot entrou em modo de escuta ativa em {channel.name}")
        except Exception as e:
            await ctx.send(f"❌ Erro ao conectar: {e}")
            logger.error(f"Join Error: {e}", exc_info=True)

    async def finished_callback(self, sink, *args):
        # Chamado quando a gravação para (bot sai do canal)
        logger.info("Gravação finalizada e bot desconectado.")

    @commands.command(name="leave")
    async def leave(self, ctx):
        """Sai do canal de voz e para de ouvir."""
        if ctx.voice_client:
            ctx.voice_client.stop_recording() # Para o Sink
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Saindo do canal de voz.")
        else:
            await ctx.send("⚠️ Não estou em nenhum canal de voz.")
