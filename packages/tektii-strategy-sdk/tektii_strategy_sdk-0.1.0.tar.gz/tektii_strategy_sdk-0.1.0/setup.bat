@echo off
REM Setup script for tektii-strategy-sdk on Windows

echo Setting up tektii-strategy-sdk...

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

echo Python detected

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Install protobuf tools
echo Installing protobuf tools...
pip install grpcio-tools mypy-protobuf

REM Create proto output directory
echo Creating proto output directory...
if not exist "tektii_sdk\proto" mkdir tektii_sdk\proto

REM Generate proto files
echo Generating proto files...
python -m grpc_tools.protoc -Iproto --python_out=tektii_sdk/proto --grpc_python_out=tektii_sdk/proto proto/strategy.proto

REM Create __init__.py in proto directory
echo. > tektii_sdk\proto\__init__.py

REM Install package in development mode
echo Installing package in development mode...
pip install -e .

REM Ask about dev dependencies
set /p install_dev="Install development dependencies? (y/n): "
if /i "%install_dev%"=="y" (
    pip install -e ".[dev,examples]"

    REM Install pre-commit hooks if available
    where pre-commit >nul 2>&1
    if %errorlevel% equ 0 (
        pre-commit install
        echo Pre-commit hooks installed
    )
)

echo.
echo Setup complete!
echo.
echo To activate the virtual environment, run:
echo   venv\Scripts\activate
echo.
echo To run tests:
echo   pytest tests\
echo.
echo To run an example:
echo   python examples\simple_ma_strategy.py
echo.
