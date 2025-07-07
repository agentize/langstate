@echo off
REM Quick setup script for Khandhas development environment (Windows)

echo 🚀 Setting up Khandhas development environment...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.9+ first.
    pause
    exit /b 1
)

echo 🐍 Using Python:
python --version

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
) else (
    echo 📦 Virtual environment already exists
)

REM Activate virtual environment and install dependencies
echo ⚙️  Installing dependencies...
call .venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install the package in development mode
cd packages\python-lib
python -m pip install -e ".[dev]"
cd ..\..

REM Verify installation
echo 🔍 Verifying installation...
python -c "import khandhas; print(f'✅ Khandhas {khandhas.__version__} installed successfully')"

REM Run a quick test
echo 🧪 Running quick test...
cd packages\python-lib
python -m pytest tests\ -q --tb=no
cd ..\..

echo.
echo 🎉 Setup complete!
echo.
echo To activate the virtual environment:
echo   .venv\Scripts\activate.bat
echo.
echo To try the sample app:
echo   cd sample-app
echo   python main.py
echo.
echo To run tests:
echo   cd packages\python-lib
echo   pytest
echo.
echo To verify everything works:
echo   python packages\python-lib\verify.py

pause
