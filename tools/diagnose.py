# diagnose.py
import os
import sys
import torch
import logging
import asyncio

# Setup bot paths
sys.path.append(os.path.join(os.getcwd(), "bot_discord"))

from core.database import DatabaseManager
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
        await db.close()
    except Exception as e:
        print(f"[ERROR] Database failure: {e}")

    # 3. Model Assets Check
    data_dir = os.path.join("bot_discord", "data")
    assets = {
        "Llama GGUF": "models" 
    }
    for name, path in assets.items():
        full_path = os.path.join(data_dir, path)
        exists = os.path.exists(full_path)
        print(f"Asset '{name}': {'OK' if exists else 'MISSING'}")

    print("\n=== Diagnostic Complete ===")

if __name__ == "__main__":
    asyncio.run(run_diag())
