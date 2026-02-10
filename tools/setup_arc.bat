@echo off
SETLOCAL EnableDelayedExpansion
title Agent-DC-Bot Setup (B580 Native XPU Optimized)

echo ====================================================
echo        Intel Arc (XPU) Setup via UV
echo        B580 BATTLEMAGE OPTIMIZED - v4
echo ====================================================

:: 1. Search for Visual Studio using vswhere (The standard way)
echo [INFO] Procurando Visual Studio via vswhere...
set "VS_INSTALL_DIR="
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"

if exist "%VSWHERE%" (
    for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do (
        set "VS_INSTALL_DIR=%%i"
    )
)

if not defined VS_INSTALL_DIR (
    :: Fallback para o seu caminho especifico se o vswhere falhar
    if exist "C:\Program Files (x86)\Microsoft Visual Studio\2022" (
        for /d %%D in ("C:\Program Files (x86)\Microsoft Visual Studio\2022\*") do (
            if exist "%%D\VC\Auxiliary\Build\vcvars64.bat" (
                set "VS_INSTALL_DIR=%%D"
            )
        )
    )
)

if defined VS_INSTALL_DIR (
    set "VCVARS=%VS_INSTALL_DIR%\VC\Auxiliary\Build\vcvars64.bat"
    if exist "!VCVARS!" (
        echo [SUCCESS] VS encontrado em: !VS_INSTALL_DIR!
        call "!VCVARS!"
    ) else (
        echo [ERROR] vcvars64.bat nao encontrado em !VS_INSTALL_DIR!
        pause
        exit /b
    )
) else (
    echo [ERROR] Nenhuma instalacao valida do Visual Studio C++ encontrada.
    echo Certifique-se de ter o "Desenvolvimento para Desktop com C++" instalado.
    pause
    exit /b
)

:: 2. Load Intel Environment
set "ONEAPI_VARS=C:\Program Files (x86)\Intel\oneAPI\setvars.bat"
if exist "%ONEAPI_VARS%" (
    echo [INFO] Carregando OneAPI Environment...
    call "%ONEAPI_VARS%" intel64
) else (
    echo [ERROR] Intel OneAPI Base Toolkit nao encontrado.
    pause
    exit /b
)

:: 3. Create/Reset Virtual Environment
echo.
echo [INFO] Preparando ambiente virtual (Python 3.11)...
if exist ".venv" rmdir /s /q .venv
uv venv --python 3.11
call .venv\Scripts\activate

:: 4. Install Native PyTorch XPU Nightly (Forced)
echo.
echo [INFO] Instalando PyTorch NATIVE XPU Nightly...
:: Forçamos a versão Nightly e usamos o index XPU como PRIORIDADE MÁXIMA
uv pip install --pre torch torchvision --index-url https://download.pytorch.org/whl/nightly/xpu --no-cache

:: 5. Compile Llama-cpp-python (SYCL)
echo.
echo [INFO] Compilando Llama.cpp para Intel Arc (SYCL)...
set "CMAKE_ARGS=-DGGML_SYCL=ON -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx -DGGML_SYCL_F16=ON"
set "FORCE_CMAKE=1"
:: Usamos Ninja se estiver no PATH para garantir compilação paralela rápida
uv pip install llama-cpp-python --no-binary llama-cpp-python --no-cache --verbose

:: 6. Install Remaining Dependencies
echo.
echo [INFO] Instalando dependencias restantes...
uv pip install -r requirements_arc.txt

echo.
echo ====================================================
echo        SETUP COMPLETO (B580 NATIVE ACTIVATED)
echo ====================================================
echo Verificando instalacao do PyTorch XPU...
python -c "import torch; print(f'Torch version: {torch.__version__}'); print(f'XPU available: {torch.xpu.is_available()}'); print(f'Device count: {torch.xpu.device_count()}')"
pause
