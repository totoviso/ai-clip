@echo off
:: ClipMaster - Self-hosted video clipping software with YouTube integration
:: This batch file runs the ClipMaster application

echo Starting ClipMaster...

:: Set the working directory to the location of this batch file
cd /d "%~dp0"

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in the PATH.
    echo Please install Python 3.8 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check if the virtual environment exists, create it if it doesn't
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate the virtual environment
call venv\Scripts\activate

:: Install or update dependencies
echo Installing dependencies...

:: First try to install everything
pip install -r requirements.txt
if %errorlevel% equ 0 (
    echo Dependencies installed successfully.
) else (
    echo Some dependencies failed to install. Trying alternative methods...
    
    :: Try installing dlib-bin specifically for Windows
    echo Installing pre-built dlib for Windows...
    pip install dlib-bin
    if %errorlevel% neq 0 (
        echo.
        echo ======================================================================
        echo WARNING: Could not install dlib-bin. Face tracking may not work.
        echo.
        echo If you want to use face tracking features, you need to:
        echo 1. Install CMake from https://cmake.org/download/
        echo 2. Make sure CMake is added to your PATH
        echo 3. Run: pip install dlib
        echo ======================================================================
        echo.
        echo Continuing with installation of other dependencies...
    )
    
    :: Install other dependencies without dlib
    pip install python-dotenv pydantic yt-dlp openai-whisper torch torchaudio nltk spacy transformers opencv-python moviepy PyQt6 qt-material requests
)

:: Download required NLTK data
echo Downloading NLTK data...
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('vader_lexicon', quiet=True)"

:: Download spaCy model
echo Downloading spaCy model...
python -m spacy download en_core_web_sm --quiet

:: Run the application
echo Starting application...
python src\main.py
if %errorlevel% neq 0 (
    echo Application exited with an error.
    pause
    exit /b 1
)

:: Deactivate the virtual environment
call venv\Scripts\deactivate

echo ClipMaster closed.
pause
