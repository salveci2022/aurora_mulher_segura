@echo off
echo ====================================
echo 🚀 INICIANDO AURORA MULHER SEGURA
echo ====================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python nao encontrado!
    echo Instale Python em: https://www.python.org/downloads/
    pause
    exit /b
)

REM Criar ambiente virtual se não existir
if not exist venv (
    echo 📦 Criando ambiente virtual...
    python -m venv venv
)

REM Ativar ambiente
echo 🔵 Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Instalar dependências
echo 📥 Instalando dependencias...
pip install -r requirements.txt

REM Mostrar IP da máquina
echo.
echo 🌐 IPs desta maquina:
ipconfig | findstr IPv4
echo.

REM Iniciar servidor
echo.
echo 🟢 Iniciando servidor...
echo.
echo ====================================
echo ACESSE EM OUTRO DISPOSITIVO:
echo http://192.168.15.93:5000
echo ====================================
echo.

python app.py

pause