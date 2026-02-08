# test_voice_hardware.py
import os
import sys
import time
import logging

# Adiciona o path do bot
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot_discord.core.voice_engine import VoiceEngine
from bot_discord.core.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VoiceTest")

def test_qwen_loading():
    logger.info("=== Teste de Carga de Hardware: Qwen3-1.7B-TTS GGUF ===")
    
    # Mock da config
    config = Config()
    
    start_time = time.time()
    engine = VoiceEngine(config)
    
    if engine.tts and engine.tts.llm:
        load_time = time.time() - start_time
        logger.info(f"[SUCCESS] Modelo carregado em {load_time:.2f}s")
        
        # Verificar se está na GPU (via llama-cpp logs internos ou checagem de camadas)
        # Se n_gpu_layers > 0 e carregou sem erro, o SYCL está ativo.
        logger.info("[INFO] Verificando integridade da engine...")
        
        test_text = "Olá, eu sou o seu agente de voz rodando nativamente na Intel Arc B580."
        try:
            # Teste de geração (síncrono no teste)
            audio = engine.tts.generate(test_text)
            if audio:
                logger.info(f"[SUCCESS] Geração de áudio completa ({len(audio)} bytes)")
            else:
                logger.error("[FAILURE] Geração retornou vazio.")
        except Exception as e:
            logger.error(f"[ERROR] Erro durante a inferência: {e}")
    else:
        logger.error("[FAILURE] Engine TTS não foi inicializada. Verifique se o arquivo .gguf existe em data/models/")

if __name__ == "__main__":
    test_qwen_loading()
