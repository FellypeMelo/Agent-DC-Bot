# voice_engine.py
import logging
import os
import asyncio
import torch
import numpy as np
from typing import Optional, Dict, Any
from core.logger import setup_logger

logger = setup_logger("core.voice_engine")

# Add espeak-ng to PATH for Kokoro phonemization
espeak_bin_path = r"C:\Program Files\eSpeak NG"
if os.path.exists(espeak_bin_path) and espeak_bin_path not in os.environ["PATH"]:
    os.environ["PATH"] += os.pathsep + espeak_bin_path
    logger.debug(f"Added {espeak_bin_path} to PATH")

# Attempt to import native kokoro
try:
    from kokoro import KPipeline
    logger.debug("kokoro (native PyTorch) package imported successfully.")
except ImportError:
    KPipeline = None
    logger.warning("kokoro package not found. Fast TTS will be disabled.")

try:
    from faster_whisper import WhisperModel
    logger.debug("faster_whisper package imported successfully.")
except ImportError:
    WhisperModel = None
    logger.warning("faster_whisper package not found. STT functionality will be disabled.")

# Opus Library Loading (Crucial for Windows)
import discord
if os.name == 'nt' and not discord.opus.is_loaded():
    logger.info("Tentando localizar biblioteca Opus para Windows...")
    try:
        # Tenta localizar a DLL no site-packages do discord
        import importlib.util
        spec = importlib.util.find_spec("discord")
        if spec and spec.submodule_search_locations:
            discord_path = spec.submodule_search_locations[0]
            opus_dll = os.path.join(discord_path, "bin", "libopus-0.x64.dll")
            if os.path.exists(opus_dll):
                discord.opus.load_opus(opus_dll)
                logger.info(f"✅ Opus carregado com sucesso de: {opus_dll}")
            else:
                logger.warning(f"⚠️ libopus-0.x64.dll não encontrada em {opus_dll}")
    except Exception as e:
        logger.error(f"❌ Falha ao carregar Opus manualmente: {e}")

class BargeInEngine:
    """
    Voice Activity Detection (VAD) Engine using the official Silero library.
    """
    def __init__(self):
        logger.info("Initializing BargeInEngine (Silero VAD).")
        try:
            # Official silero-vad package way of loading
            from silero_vad import load_silero_vad
            self.model = load_silero_vad()
            logger.info("Silero VAD (Official Library) loaded.")
        except Exception as e:
            logger.error(f"Failed to load Silero VAD library: {e}", exc_info=True)
            self.model = None

    def _energy_based_vad(self, audio_chunk: np.ndarray, threshold: float = 0.015) -> bool:
        """
        Fallback VAD based on RMS energy.
        """
        try:
            # Calculate Root Mean Square
            if audio_chunk.dtype == np.int16:
                # Normalize int16 to -1.0 to 1.0 range for consistency
                # Use mean of squares on int32 to avoid overflow, then sqrt, then normalize?
                # Faster: convert to float only if needed.
                # Let's stick to simple float conversion for clarity and correctness
                chunk_float = audio_chunk.astype('float32') / 32768.0
            else:
                chunk_float = audio_chunk

            rms = np.sqrt(np.mean(chunk_float**2))
            print(f"Energy VAD: RMS={rms:.4f} Threshold={threshold}"); print(f"Energy VAD: RMS={rms:.4f} Threshold={threshold}"); return rms > threshold
        except Exception as e:
            logger.error(f"Energy VAD error: {e}")
            return False

    def is_speech(self, audio_chunk: np.ndarray, threshold: float = 0.5) -> bool:
        """
        Detects if speech is present in the chunk.
        
        Big(O): O(1) real-time inference.
        """
        if self.model is None:
            # Fallback to Energy-based VAD
            return self._energy_based_vad(audio_chunk)
        
        try:
            import torch
            
            # Convert to torch tensor (Expected by the library)
            if audio_chunk.dtype == np.int16:
                audio_chunk = audio_chunk.astype('float32') / 32768.0
            
            tensor = torch.from_numpy(audio_chunk)
            if tensor.ndim == 1:
                tensor = tensor.unsqueeze(0) # Add batch dim if needed
            
            # Use the library's official detection method (probability based for real-time)
            # Official silero-vad v4/v5 returns probability when called directly
            with torch.no_grad():
                confidence = self.model(tensor, 16000).item()
            
            is_speech_detected = confidence > threshold
            if is_speech_detected:
                logger.debug(f"VAD: Speech detected! Confidence: {confidence:.2f}")
            return is_speech_detected
        except Exception as e:
            logger.error(f"VAD Inference error: {e}")
            # Fallback on error too
            return self._energy_based_vad(audio_chunk)

class VoiceEngine:
    """
    Fast TTS Engine (Kokoro).
    Optimized for Intel Arc B580 (XPU) and low-latency interaction.
    """

    def __init__(self, config):
        self.config = config
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.device = "xpu" if torch.xpu.is_available() else "cpu"
        
        # Fast Engine (Kokoro)
        self.kokoro: Optional[KPipeline] = None
        self.kokoro_voice = "af_sky" # Default feminine clear voice
        
        self.whisper_model: Optional[Any] = None
        logger.info(f"VoiceEngine initialized. Device: {self.device}")
        
        # VAD Initialization
        self.vad = BargeInEngine()

    async def load_kokoro(self):
        """Carrega o Kokoro-82M nativo (PyTorch) via KPipeline."""
        if self.kokoro: 
            logger.debug("[KOKORO] Motor já carregado.")
            return

        if KPipeline is None:
            logger.error("[KOKORO] Biblioteca 'kokoro' não disponível.")
            return
        
        logger.info("========================================")
        logger.info("   INICIANDO KOKORO TTS (PYTORCH)       ")
        logger.info("========================================")

        try:
            import time
            start = time.time()
            logger.debug(f"[KOKORO] Instanciando KPipeline no dispositivo {self.device}...")
            
            # 'p' para Português, 'a' para American English, etc.
            self.kokoro = KPipeline(lang_code='p', device=self.device)
            
            end = time.time()
            logger.info(f"✅ Kokoro PyTorch carregado com sucesso em {end-start:.2f}s.")
        except Exception as e:
            logger.error(f"❌ FALHA no carregamento do Kokoro PyTorch: {e}", exc_info=True)

    async def load_stt(self):
        """Carrega o modelo Whisper para STT."""
        if self.whisper_model: return
        
        if WhisperModel is None:
            logger.error("faster-whisper package not found.")
            return

        # Whisper (faster-whisper) não suporta 'xpu' nativamente sem hacks complexos.
        # Usamos CPU para Whisper pois o modelo 'tiny' é extremamente leve.
        whisper_device = "cpu"
        logger.info(f"Loading Whisper (tiny) into {whisper_device} for low latency...")
        try:
            self.whisper_model = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: WhisperModel("tiny", device=whisper_device, compute_type="int8")
            )
            logger.info("Whisper loaded successfully on CPU.")
        except Exception as e:
            logger.error(f"Failed to load Whisper: {e}")

    async def transcribe(self, audio_data: np.ndarray) -> str:
        """Converte áudio em texto usando Whisper."""
        if not self.whisper_model:
            await self.load_stt()
        
        if not self.whisper_model: return ""

        loop = asyncio.get_event_loop()
        try:
            # Whisper espera float32 entre -1 e 1
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype('float32') / 32768.0
            
            # Transcription logic
            segments, info = await loop.run_in_executor(None, lambda: self.whisper_model.transcribe(audio_data, language="pt"))
            text = " ".join([s.text for s in segments]).strip()
            return text
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

    async def load_engine(self):
        """Pre-loads the Kokoro engine."""
        await self.load_kokoro()

    async def unload_engine(self):
        """Purges models from VRAM/RAM."""
        if self.kokoro:
            logger.info("Unloading Kokoro Engine...")
            self.kokoro = None
            if self.device == "xpu":
                torch.xpu.empty_cache()

    async def generate_speech(self, text: str, sentiment: str = "neutral") -> Optional[bytes]:
        """
        Generates speech using Kokoro.
        """
        return await self._generate_kokoro(text)

    async def _generate_kokoro(self, text: str) -> Optional[bytes]:
        """Geração via Kokoro V1.0 com telemetria detalhada."""
        if not self.kokoro:
            logger.debug("[KOKORO] Motor não carregado. Tentando carregar...")
            await self.load_kokoro()
            if not self.kokoro: 
                logger.error("[KOKORO] Abortando: motor não pôde ser carregado.")
                return None

        logger.info(f"--- [INÍCIO SÍNTESE V1.0] ---")
        logger.info(f"Texto: '{text[:100]}...'")
        import time
        start_time = time.time()

        try:
            # Forçamos pt-br para o Kokoro V1.0
            # Kokoro PyTorch pipeline pattern
            # generator retorna (graphemes, phonemes, audio)
            generator = self.kokoro(
                text, 
                voice=self.kokoro_voice, 
                speed=1.0
            )
            
            # Coletamos o áudio (podemos concatenar se houver múltiplos chunks)
            all_samples = []
            for gs, ps, audio in generator:
                if audio is not None:
                    all_samples.append(audio)
            
            if not all_samples:
                logger.error("❌ Erro: Kokoro não gerou nenhum áudio.")
                return None
            
            samples = np.concatenate(all_samples)
            sr = 24000 # Kokoro nativo é fixo em 24kHz
            
            gen_time = time.time() - start_time
            logger.info(f"✅ SUCESSO: Áudio gerado em {gen_time:.3f}s")
            logger.info(f"[STATS] Samples: {len(samples)} | SR Original: {sr}Hz")
            
            # Resampling para 48000Hz Stereo (Discord)
            if sr != 48000:
                logger.debug(f"[AUDIO] Resampling {sr}Hz -> 48000Hz...")
                num_samples = int(len(samples) * 48000 / sr)
                # Optimization: Use float32 for interpolation indices
                audio = np.interp(
                    np.linspace(0, len(samples), num_samples, dtype=np.float32),
                    np.arange(len(samples), dtype=np.float32),
                    samples
                )
            else:
                audio = samples

            # Stereo interleaving (Optimized: Convert to Int16 first)
            logger.debug("[AUDIO] Convertendo Mono -> Stereo Interleaved...")
            
            # Scale and cast to int16 once (Mono)
            audio_int16 = (audio * 32767).astype(np.int16)

            # Interleave into pre-allocated stereo buffer
            audio_stereo = np.empty(len(audio_int16) * 2, dtype=np.int16)
            audio_stereo[0::2] = audio_int16
            audio_stereo[1::2] = audio_int16

            final_pcm = audio_stereo.tobytes()
            logger.info(f"✅ [SÍNTESE COMPLETA] {len(final_pcm)} bytes preparados.")
            return final_pcm

        except Exception as e:
            logger.error(f"❌ ERRO NA SÍNTESE KOKORO: {e}", exc_info=True)
            return None
