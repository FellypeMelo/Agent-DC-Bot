# voice_engine.py
import logging
import os
import asyncio
import torch
import numpy as np
from typing import Optional, Dict, Any
from core.logger import setup_logger

logger = setup_logger("core.voice_engine")

# Attempt to import kokoro-onnx
try:
    from kokoro_onnx import Kokoro
    logger.debug("kokoro_onnx package imported successfully.")
except ImportError:
    Kokoro = None
    logger.warning("kokoro_onnx package not found. Fast TTS will be disabled.")

# Attempt to import qwen_tts
try:
    from qwen_tts import Qwen3TTSModel
    logger.debug("qwen_tts package imported successfully.")
except ImportError:
    Qwen3TTSModel = None
    logger.warning("qwen_tts package not found. High-quality TTS will be disabled.")

try:
    from faster_whisper import WhisperModel
    logger.debug("faster_whisper package imported successfully.")
except ImportError:
    WhisperModel = None
    logger.warning("faster_whisper package not found. STT functionality will be disabled.")

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
    Dual-Engine TTS (Kokoro for Speed, Qwen3 for Quality).
    Optimized for Intel Arc B580 (XPU) and low-latency interaction.
    """

    def __init__(self, config):
        self.config = config
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.device = "xpu" if torch.xpu.is_available() else "cpu"
        
        # Fast Engine (Kokoro)
        self.kokoro: Optional[Kokoro] = None
        self.kokoro_voice = "af_sky" # Default feminine clear voice
        
        # High Quality Engine (Qwen)
        self.model: Optional[Any] = None
        self.cached_prompts: Dict[str, Any] = {}
        self.base_model_id = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
        self.design_model_id = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
        
        self.whisper_model: Optional[Any] = None
        logger.info(f"VoiceEngine initialized. Device: {self.device}")
        
        # VAD Initialization
        self.vad = BargeInEngine()

    async def load_kokoro(self):
        """Carrega o Kokoro-TTS V1.0 ONNX com logs detalhados."""
        if self.kokoro: 
            logger.debug("[KOKORO] Motor já carregado.")
            return
        
        # Caminho estrito solicitado pelo usuário
        v1_folder = os.path.join(self.base_path, "data", "tts", "Kokoro-82M-v1.0-ONNX")
        model_path = os.path.join(v1_folder, "onnx", "model_q8f16.onnx")
        voices_path = os.path.join(self.base_path, "data", "tts", "kokoro", "voices.json")
        
        logger.info("========================================")
        logger.info("   INICIANDO KOKORO TTS V1.0 (ONNX)     ")
        logger.info("========================================")
        logger.info(f"[DEBUG] Pasta Base: {v1_folder}")
        logger.info(f"[DEBUG] Modelo: {model_path}")
        logger.info(f"[DEBUG] Vozes: {voices_path}")

        if not os.path.exists(model_path):
            logger.error(f"[CRÍTICO] Modelo ONNX V1.0 NÃO ENCONTRADO em: {model_path}")
            return
        if not os.path.exists(voices_path):
            logger.warning(f"[AVISO] voices.json não encontrado em {voices_path}. Tentando fallback...")
            alt_voices = os.path.join(v1_folder, "voices.json")
            if os.path.exists(alt_voices):
                voices_path = alt_voices
                logger.info(f"[DEBUG] Usando voices.json alternativo: {voices_path}")
            else:
                logger.error("[CRÍTICO] Nenhum arquivo voices.json disponível para Kokoro.")
                return

        try:
            import time
            start = time.time()
            logger.debug("[KOKORO] Instanciando classe Kokoro...")
            self.kokoro = Kokoro(model_path, voices_path)
            end = time.time()
            logger.info(f"✅ Kokoro V1.0 carregado com sucesso em {end-start:.2f}s.")
            logger.info(f"[INFO] Backend ONNX Providers: {self.kokoro.get_providers() if hasattr(self.kokoro, 'get_providers') else 'N/A'}")
        except Exception as e:
            logger.error(f"❌ FALHA TOTAL no carregamento do Kokoro V1.0: {e}", exc_info=True)

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

    def is_loaded(self) -> bool:
        """Checks if the model is currently in VRAM."""
        return self.kokoro is not None or self.model is not None

    async def load_engine(self, mode: str = "base"):
        """Loads the Qwen3 model into VRAM."""
        if mode == "fast":
            await self.load_kokoro()
            return

        import shutil
        if not shutil.which("sox"):
            logger.error("ERRO CRÍTICO: SoX não encontrado no PATH. O Qwen-TTS precisa do SoX instalado.")
            return

        if Qwen3TTSModel is None:
            logger.error("qwen-tts package not found. TTS disabled.")
            return

        if self.model:
            logger.debug(f"Qwen3-TTS model already loaded in {mode} mode.")
            return 

        repo_id = self.base_model_id if mode == "base" else self.design_model_id
        logger.info(f"Loading Qwen3-TTS model '{repo_id}' ({mode} mode) into {self.device}...")
        
        loop = asyncio.get_event_loop()
        try:
            self.model = await loop.run_in_executor(None, lambda: Qwen3TTSModel.from_pretrained(
                repo_id,
                device_map=self.device,
                dtype=torch.float16, 
                attn_implementation="eager"
            ))
            logger.info(f"Qwen3-TTS model '{repo_id}' loaded successfully on {self.device}.")
        except Exception as e:
            logger.error(f"Failed to load TTS model '{repo_id}': {e}", exc_info=True)
            self.model = None

    async def unload_engine(self):
        """Purges models from VRAM/RAM."""
        if self.model:
            logger.info("Unloading Qwen3-TTS Engine...")
            del self.model
            self.model = None
            if self.device == "xpu":
                torch.xpu.empty_cache()
        if self.kokoro:
            logger.info("Unloading Kokoro Engine...")
            self.kokoro = None

    async def load_dna(self, dna_blob: bytes):
        """Loads voice DNA for Qwen3."""
        import pickle
        try:
            self.cached_prompts['active_dna'] = pickle.loads(dna_blob)
            logger.info("Voice DNA loaded from database.")
        except Exception as e:
            logger.error(f"Failed to load voice DNA: {e}", exc_info=True)

    async def generate_speech(self, text: str, sentiment: str = "neutral") -> Optional[bytes]:
        """
        Generates speech using Kokoro (Fast) or Qwen (Quality).
        """
        # Preferência por Kokoro se carregado (Ultra Rápido)
        if self.kokoro:
            return await self._generate_kokoro(text)
        
        return await self._generate_qwen(text, sentiment)

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
            logger.debug(f"[KOKORO] Gerando áudio com voz '{self.kokoro_voice}'...")
            
            # Kokoro-ONNX v0.5 generator pattern
            samples, sr = next(self.kokoro.create(
                text, 
                voice=self.kokoro_voice, 
                speed=1.0, 
                lang="pt-br" 
            ))
            
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

        except StopIteration:
            logger.error("❌ Erro: O gerador Kokoro não retornou nenhum áudio.")
            return None
        except Exception as e:
            logger.error(f"❌ ERRO NA SÍNTESE V1.0: {e}", exc_info=True)
            return None

    async def _generate_qwen(self, text: str, sentiment: str = "neutral") -> Optional[bytes]:
        """Geração via Qwen3-TTS (Alta Qualidade)."""
        logger.info(f"Generating high-quality speech for: '{text[:50]}...'")
        if not self.model:
            await self.load_engine(mode="base")
            if not self.model: return None

        prompt = self.cached_prompts.get('active_dna')
        if not prompt:
            logger.error("No DNA found. Using Kokoro as fallback.")
            await self.load_kokoro()
            return await self._generate_kokoro(text)

        loop = asyncio.get_event_loop()
        try:
            wavs, sr = await loop.run_in_executor(None, lambda: self.model.generate_voice_clone(
                text=text,
                language="Portuguese",
                voice_clone_prompt=prompt,
                x_vector_only_mode=True
            ))
            
            if not wavs: return None
            audio = wavs[0]
            
            if sr != 48000:
                num_samples = int(len(audio) * 48000 / sr)
                audio = np.interp(
                    np.linspace(0, len(audio), num_samples, dtype=np.float32),
                    np.arange(len(audio), dtype=np.float32),
                    audio
                )
            
            # Optimized Stereo Mix
            audio_int16 = (audio * 32767).astype(np.int16)
            audio_stereo = np.empty(len(audio_int16) * 2, dtype=np.int16)
            audio_stereo[0::2] = audio_int16
            audio_stereo[1::2] = audio_int16
            return audio_stereo.tobytes()
        except Exception as e:
            logger.error(f"Qwen TTS Error: {e}")
            return None

    async def design_and_cache_voice(self, name: str, description: str):
        """
        One-time setup: Designs a voice and caches its embedding (prompt).
        
        Args:
            name (str): Key for the personality (e.g., 'brazilian').
            description (str): Natural language description (e.g., 'Feminina, jovem, animada').
        """
        logger.info(f"Starting voice design process for persona '{name}' with description: '{description}'")
        # 1. Temporarily load design model
        logger.debug("Loading 'design' engine.")
        await self.load_engine(mode="design")
        
        ref_text = "Olá! Eu estou testando a minha nova voz configurada especialmente para você."
        logger.debug(f"Generating reference audio for voice design with text: '{ref_text}'")
        
        loop = asyncio.get_event_loop()
        try:
            wavs, sr = await loop.run_in_executor(None, lambda: self.model.generate_voice_design(
                text=ref_text,
                language="Portuguese",
                instruct=description
            ))
            logger.info(f"Reference audio generated for voice design. WAVs count: {len(wavs)}, Sample Rate: {sr}.")
            
            # 2. Extract Clone Prompt (This is what we actually save)
            # We switch to base model to extract the reusable prompt
            logger.debug("Unloading design engine and loading base engine to extract clone prompt.")
            await self.unload_engine()
            await self.load_engine(mode="base")
            
            prompt = await loop.run_in_executor(None, lambda: self.model.create_voice_clone_prompt(
                ref_audio=(wavs[0], sr),
                x_vector_only_mode=True # Precomputed embeddings for speed
            ))
            
            self.cached_prompts[name] = prompt
            logger.info(f"Voice persona '{name}' created and cached.")
            return prompt
        except Exception as e:
            logger.error(f"Voice design and caching failed for '{name}': {e}", exc_info=True)
            await self.unload_engine() # Ensure any loaded model is unloaded in case of failure
            return None
