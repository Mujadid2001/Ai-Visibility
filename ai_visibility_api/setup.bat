@echo off
REM Setup script for AI Visibility API (Windows)

echo 🚀 AI Visibility Intelligence API - Setup
echo ==========================================

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python version: %PYTHON_VERSION%

REM Create virtual environment
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
) else (
    echo ✓ Virtual environment already exists
)

REM Activate venv
call venv\Scripts\activate.bat
echo ✓ Virtual environment activated

REM Install dependencies
echo 📚 Installing dependencies...
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

REM Copy .env if doesn't exist
if not exist ".env" (
    echo ⚙️  Creating .env file from .env.example
    copy .env.example .env
    echo ⚠️  IMPORTANT: Edit .env and add your OPENAI_API_KEY or ANTHROPIC_API_KEY
) else (
    echo ✓ .env file already exists
)

REM Initialize database
echo 🗄️  Initializing database...
python -c "from app import create_app, db; app = create_app(); db.create_all()" 2>nul
if errorlevel 0 echo ✓ Database initialized

echo.
echo ✅ Setup complete!
echo.
echo Next steps:
echo 1. Edit .env and add your API keys
echo 2. Run: python run.py
echo 3. Visit: http://localhost:5000/health
echo.
