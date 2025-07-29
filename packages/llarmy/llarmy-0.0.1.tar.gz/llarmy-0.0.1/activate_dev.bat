@echo off
echo 🚀 Activating llarmy development environment...

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Set PYTHONPATH to include src
set PYTHONPATH=%CD%\src;%PYTHONPATH%

echo ✅ Virtual environment activated
echo 📁 PYTHONPATH configured to include src/
echo.
echo 📋 Available commands:
echo   python scripts/setup_dev.py  - Setup development dependencies
echo   python scripts/lint.py       - Run linting
echo   python scripts/test.py       - Run tests  
echo   python scripts/format.py     - Format code
echo   python scripts/build.py      - Build package
echo.
echo 🎯 Ready for development!

REM Keep the command prompt open
cmd /k 