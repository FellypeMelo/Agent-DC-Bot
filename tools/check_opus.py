import discord
import os
import sys

# Setup bot paths
sys.path.append(os.path.join(os.getcwd(), "bot_discord"))
from core.database import DatabaseManager
from core.config import Config
from core.voice_engine import VoiceEngine

print(f"Discord Version: {discord.__version__}")
# The import above should have triggered voice_engine's top-level opus loader
print(f"Opus Loaded (via VoiceEngine): {discord.opus.is_loaded()}")
