# download_assets.py
import os
import requests
from huggingface_hub import snapshot_download

def download_assets():
    print("=== Agent-DC-Bot: Downloading Production Assets ===")
    
    data_dir = os.path.join("bot_discord", "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # 1. Qwen3-TTS
    qwen_dir = os.path.join(data_dir, "tts", "qwen3")
    if not os.path.exists(os.path.join(qwen_dir, "config.json")):
        print("[INFO] Downloading Qwen3-TTS-1.7B...")
        snapshot_download(
            repo_id="Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
            local_dir=qwen_dir,
            local_dir_use_symlinks=False
        )

    # 2. Kokoro-TTS (Skip download, using manually cloned V1.0)
    print("[INFO] Kokoro-TTS V1.0: Manually cloned repo detected. Skipping auto-download.")

    # 3. Silero VAD (Production Stable URL)
    vad_path = os.path.join(data_dir, "silero_vad.onnx")
    if not os.path.exists(vad_path):
        print("[INFO] Downloading Silero VAD...")
        # Direct URL from the official Silero releases
        url = "https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.onnx"
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                with open(vad_path, 'wb') as f:
                    f.write(r.content)
                print("[SUCCESS] Silero VAD ready.")
            else:
                # Emergency Fallback to HuggingFace version if GitHub fails
                print("[INFO] GitHub failed, trying HuggingFace fallback...")
                from huggingface_hub import hf_hub_download
                hf_hub_download(repo_id="NeuML/kokoro-base-onnx", filename="silero_vad.onnx", local_dir=data_dir)
        except Exception as e:
            print(f"[ERROR] VAD Download failed: {e}")

    print("\n[SUCCESS] Asset check complete.")

if __name__ == "__main__":
    download_assets()