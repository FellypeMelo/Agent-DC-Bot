@echo off
setlocal enabledelayedexpansion
title "Agent-DC-Bot - UV Native Production Launcher"

echo ====================================================
echo       AGENT-DC-BOT: INTEL ARC B580 (UV NATIVE)
echo ====================================================

:: 1. Self-Correction: Ensure requirements are synced
echo [INFO] Verificando integridade do ambiente (UV Sync)...
uv pip install -r tools/requirements_arc.txt --quiet

:: 2. Check for .env
if not exist "bot_discord\.env" goto setup_wizard
goto check_voice

:setup_wizard
echo [SETUP] Iniciando Arquiteto de Ambiente...
:: (Interactive setup logic remains the same as before...)
set /p DISCORD_TOKEN="[?] Digite o seu DISCORD BOT TOKEN: "
set /p BOT_PREFIX="[?] Digite o PREFIXO para comandos: "
echo [SETUP] Procurando modelos...
set "MODEL_COUNT=0"
for %%f in ("bot_discord\data\models\*.gguf") do (
    set /a MODEL_COUNT+=1
    set "MODEL_PATH_!MODEL_COUNT!=%%f"
    echo [!MODEL_COUNT!] %%~nxf
)
if !MODEL_COUNT! equ 0 (
    set /p CLEAN_PATH="[?] Digite o caminho do seu arquivo .gguf: "
) else (
    set /p CHOICE="[?] Escolha o numero do modelo: "
    set "LOCAL_MODEL_PATH=!MODEL_PATH_%CHOICE%!"
    set "CLEAN_PATH=!LOCAL_MODEL_PATH:\=/!"
)

echo # Configuracoes do Discord > bot_discord\.env
echo DISCORD_TOKEN=%DISCORD_TOKEN% >> bot_discord\.env
echo BOT_PREFIX=%BOT_PREFIX% >> bot_discord\.env
echo USE_LOCAL_LLM=true >> bot_discord\.env
echo LOCAL_MODEL_PATH=%CLEAN_PATH% >> bot_discord\.env
echo GPU_LAYERS=-1 >> bot_discord\.env
echo DEVICE=xpu >> bot_discord\.env
echo MEMORY_LIMIT=50 >> bot_discord\.env
echo LOG_LEVEL=INFO >> bot_discord\.env
echo [SUCCESS] .env criado.

:check_voice
:: 3. Verify Assets via the Python Downloader
echo [INFO] Verificando ativos de IA...
uv run tools/download_assets.py

:set_vars
:: 4. Set Intel Hardware Variables & Utility Paths
set "PATH=C:\Program Files (x86)\sox-14-4-2;%PATH%"
set "ONEAPI_ROOT=C:\Program Files (x86)\Intel\oneAPI"
if exist "%ONEAPI_ROOT%" (
    set "PATH=%ONEAPI_ROOT%\compiler\latest\windows\bin;%PATH%"
    set "PATH=%ONEAPI_ROOT%\mkl\latest\windows\bin;%PATH%"
    echo [INFO] Intel oneAPI detectado.
)

:launch
echo [INFO] Iniciando o Bot no modo B580...
echo ----------------------------------------------------

uv run bot_discord/core/bot.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] O Bot parou. Verifique o .env ou erros de VRAM.
    pause
)
pause