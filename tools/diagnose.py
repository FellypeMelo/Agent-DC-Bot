# diagnose.py
import os
import sys
import torch
import logging
import asyncio

# Setup bot paths
sys.path.append(os.path.join(os.getcwd(), "bot_discord"))

from core.database import DatabaseManager
from core.voice_engine import VoiceEngine
from core.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Diagnostic")

async def run_diag():
    print("=== Agent-DC-Bot Production Diagnostic ===")
    
    # 1. Hardware Check
    print(f"Python: {sys.version}")
    print(f"Torch: {torch.__version__}")
    xpu_ok = hasattr(torch, 'xpu') and torch.xpu.is_available()
    print(f"XPU (Intel GPU) Available: {xpu_ok}")
    if xpu_ok:
        print(f"Device: {torch.xpu.get_device_name(0)}")

    # 2. Database Check
    db = DatabaseManager()
    try:
        await db.connect()
        print("[SUCCESS] Database connection established.")
        # Check tables
        async with db._db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
            tables = await cursor.fetchall()
            print(f"Tables found: {[t[0] for t in tables]}")
    except Exception as e:
        print(f"[ERROR] Database failure: {e}")

    # 3. Model Assets Check
    data_dir = os.path.join("bot_discord", "data")
    assets = {
        "Qwen3 Config": "tts/qwen3/config.json",
        "Silero VAD": "silero_vad.onnx",
        "Llama GGUF": "models" # We just check folder existence
    }
    for name, path in assets.items():
        full_path = os.path.join(data_dir, path)
        exists = os.path.exists(full_path)
        print(f"Asset '{name}': {'OK' if exists else 'MISSING'}")

    # 4. Engine Load Test (VRAM Stress)
    print("
[INFO] Starting Engine Load Test (VRAM)...")
    config = Config(db)
    engine = VoiceEngine(config)
    
    # Check VAD
    if engine.vad:
        print("[SUCCESS] VAD Engine loaded.")
    else:
        print("[WARNING] VAD Engine NOT loaded. Barge-In will be disabled.")

    print("
=== Diagnostic Complete ===")

if __name__ == "__main__":
    asyncio.run(run_diag())
