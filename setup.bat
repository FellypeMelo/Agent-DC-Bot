@echo off
SETLOCAL EnableDelayedExpansion
title Agent-DC-Bot Setup (UV Generic)

echo ====================================================
echo        Generic Setup via UV (CPU/CUDA)
echo ====================================================

:: 1. Install UV
echo [INFO] Verificando UV...
powershell -Command "if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { echo 'Installing UV...'; irm https://astral.sh/uv/install.ps1 | iex }"

:: 2. Create Venv
echo [INFO] Criando venv (Python 3.11)...
uv venv --python 3.11

:: 3. Select Hardware
echo.
echo Selecione seu Hardware:
echo [1] NVIDIA GPU (CUDA)
echo [2] CPU Only
set /p gpu_choice="Opcao: "

if "%gpu_choice%"=="1" (
    echo [INFO] Instalando PyTorch CUDA Nightly...
    uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu121
    set CMAKE_ARGS=-DGGML_CUDA=ON
    uv pip install llama-cpp-python --no-binary llama-cpp-python
) else (
    echo [INFO] Instalando PyTorch CPU...
    uv pip install torch torchvision torchaudio
    uv pip install llama-cpp-python
)

:: 4. Install Deps
uv pip install -r requirements.txt

echo [SUCCESS] Setup Concluido.
pause