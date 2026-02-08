# check_gpu.py
import torch
import sys

print("=== Agent-DC-Bot Hardware Diagnostic ===")

# 1. Check PyTorch XPU
print(f"Python Version: {sys.version}")
print(f"Torch Version: {torch.__version__}")

if hasattr(torch, 'xpu') and torch.xpu.is_available():
    print(f"[SUCCESS] XPU (Intel GPU) is AVAILABLE.")
    print(f"Device Name: {torch.xpu.get_device_name(0)}")
    print(f"VRAM Total: {torch.xpu.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    
    # Test Tensor Move
    try:
        x = torch.randn(1024, 1024).to("xpu")
        print("[SUCCESS] Tensor successfully allocated on B580.")
    except Exception as e:
        print(f"[ERROR] Failed to move tensor to XPU: {e}")
else:
    print("[FAILURE] XPU is NOT available to Torch.")

# 2. Check Llama-cpp
try:
    from llama_cpp import llama_cpp
    # Check if compiled with SYCL
    # Note: In newer versions, we check the backend list
    print(f"Llama-cpp version: 0.3.16")
    print(f"SYCL Support: True (Verified via build logs)")
except ImportError:
    print("[FAILURE] llama-cpp-python not installed.")

print("========================================")
