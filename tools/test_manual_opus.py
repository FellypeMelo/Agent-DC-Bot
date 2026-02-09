import discord
import os

# Try to find the dll
site_packages = r"g:\Programas\Agent-DC-Bot\.venv\Lib\site-packages"
opus_path = os.path.join(site_packages, "discord", "bin", "libopus-0.x64.dll")

print(f"Checking if file exists at: {opus_path}")
if os.path.exists(opus_path):
    print("File found!")
    try:
        discord.opus.load_opus(opus_path)
        print(f"Opus Loaded successfully: {discord.opus.is_loaded()}")
    except Exception as e:
        print(f"Failed to load opus manually: {e}")
else:
    print("File NOT found at expected location.")

# Try alt path if needed
alt_opus_path = os.path.join(site_packages, "av.libs", "libopus-0-2ceb9cd024b0d48ea5681bed0eb39017.dll")
if not discord.opus.is_loaded() and os.path.exists(alt_opus_path):
    print(f"Trying alt path: {alt_opus_path}")
    try:
        discord.opus.load_opus(alt_opus_path)
        print(f"Opus Loaded with alt: {discord.opus.is_loaded()}")
    except Exception as e:
        print(f"Alt load failed: {e}")
