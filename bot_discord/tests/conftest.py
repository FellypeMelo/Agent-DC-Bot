import importlib
import importlib.machinery
import importlib.util
import os
import sys
import types

import numpy as np
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
BOT_ROOT = os.path.join(PROJECT_ROOT, "bot_discord")
if BOT_ROOT not in sys.path:
    sys.path.insert(0, BOT_ROOT)


def _install_stub_module(name, module):
    if name not in sys.modules:
        if getattr(module, "__spec__", None) is None:
            module.__spec__ = importlib.machinery.ModuleSpec(name, loader=None)
        sys.modules[name] = module


def _ensure_optional_dependencies():
    if importlib.util.find_spec("torch") is None:
        torch_stub = types.SimpleNamespace()

        class XPU:
            @staticmethod
            def is_available():
                return False

        class DummyNoGrad:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        torch_stub.xpu = XPU()
        torch_stub.float16 = "float16"
        torch_stub.no_grad = lambda: DummyNoGrad()
        torch_stub.from_numpy = lambda arr: arr
        _install_stub_module("torch", torch_stub)

    if importlib.util.find_spec("sentence_transformers") is None:
        sentence_stub = types.SimpleNamespace()

        class SentenceTransformer:
            def __init__(self, model_name):
                self.model_name = model_name

            def encode(self, text):
                return np.array([0.0, 1.0], dtype=np.float32)

        sentence_stub.SentenceTransformer = SentenceTransformer
        _install_stub_module("sentence_transformers", sentence_stub)

    if importlib.util.find_spec("kokoro_onnx") is None:
        kokoro_stub = types.SimpleNamespace()

        class Kokoro:
            def __init__(self, *args, **kwargs):
                pass

            def get_providers(self):
                return ["cpu"]

        kokoro_stub.Kokoro = Kokoro
        _install_stub_module("kokoro_onnx", kokoro_stub)

    if importlib.util.find_spec("qwen_tts") is None:
        qwen_stub = types.SimpleNamespace()

        class Qwen3TTSModel:
            @classmethod
            def from_pretrained(cls, *args, **kwargs):
                return cls()

        qwen_stub.Qwen3TTSModel = Qwen3TTSModel
        _install_stub_module("qwen_tts", qwen_stub)

    if importlib.util.find_spec("faster_whisper") is None:
        whisper_stub = types.SimpleNamespace()

        class WhisperModel:
            def __init__(self, *args, **kwargs):
                pass

            def transcribe(self, *args, **kwargs):
                return ([], None)

        whisper_stub.WhisperModel = WhisperModel
        _install_stub_module("faster_whisper", whisper_stub)

    if importlib.util.find_spec("silero_vad") is None:
        silero_stub = types.SimpleNamespace()

        class DummyVadModel:
            def __call__(self, *args, **kwargs):
                return np.array(0.0)

        silero_stub.load_silero_vad = lambda: DummyVadModel()
        _install_stub_module("silero_vad", silero_stub)

    if importlib.util.find_spec("discord") is None:
        discord_stub = types.SimpleNamespace()
        discord_stub.Color = types.SimpleNamespace(blue=lambda: 0x0000FF, green=lambda: 0x00FF00)

        class Embed:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
                self.fields = []

            def add_field(self, **kwargs):
                self.fields.append(kwargs)

        discord_stub.Embed = Embed
        discord_stub.PCMAudio = lambda *args, **kwargs: None
        discord_stub.sinks = types.SimpleNamespace(Sink=object)
        _install_stub_module("discord", discord_stub)

    if importlib.util.find_spec("psutil") is None:
        psutil_stub = types.ModuleType("psutil")
        psutil_stub.cpu_percent = lambda: 0.0
        psutil_stub.virtual_memory = lambda: types.SimpleNamespace(percent=0.0)
        _install_stub_module("psutil", psutil_stub)

    if importlib.util.find_spec("discord") is not None:
        discord_module = importlib.import_module("discord")
        if not hasattr(discord_module, "sinks"):
            discord_module.sinks = types.SimpleNamespace(Sink=object)


_ensure_optional_dependencies()
