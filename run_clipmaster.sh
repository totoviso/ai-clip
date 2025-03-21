#!/bin/bash
# ClipMaster - Self-hosted video clipping software with YouTube integration
# This shell script runs the ClipMaster application

echo "Starting ClipMaster..."

# Set the working directory to the location of this script
cd "$(dirname "$0")"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed or not in the PATH."
    echo "Please install Python 3.8 or higher from https://www.python.org/downloads/"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if the virtual environment exists, create it if it doesn't
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment."
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

# Activate the virtual environment
source venv/bin/activate

# Install or update dependencies
echo "Installing dependencies..."

# First try to install everything
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "Dependencies installed successfully."
else
    echo "Some dependencies failed to install. Trying alternative methods..."
    
    # Try installing dlib with specific options
    echo "Installing dlib with specific options..."
    if [ "$(uname)" == "Darwin" ]; then
        # macOS
        echo "Detected macOS. Checking for Homebrew..."
        if ! command -v brew &> /dev/null; then
            echo "Homebrew not found. Please install Homebrew from https://brew.sh/"
            echo "Then run: brew install cmake"
        else
            echo "Installing CMake via Homebrew..."
            brew install cmake
        fi
    elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
        # Linux
        echo "Detected Linux. Checking for package manager..."
        if command -v apt-get &> /dev/null; then
            echo "Installing CMake via apt..."
            sudo apt-get update
            sudo apt-get install -y cmake
        elif command -v yum &> /dev/null; then
            echo "Installing CMake via yum..."
            sudo yum install -y cmake
        else
            echo "Could not detect package manager. Please install CMake manually."
        fi
    fi
    
    # Try installing dlib again
    pip install dlib
    if [ $? -ne 0 ]; then
        echo ""
        echo "======================================================================"
        echo "WARNING: Could not install dlib. Face tracking may not work."
        echo ""
        echo "If you want to use face tracking features, you need to:"
        echo "1. Install CMake manually"
        echo "2. Make sure CMake is added to your PATH"
        echo "3. Run: pip install dlib"
        echo "======================================================================"
        echo ""
        echo "Continuing with installation of other dependencies..."
    fi
    
    # Install other dependencies without dlib
    pip install python-dotenv pydantic yt-dlp openai-whisper torch torchaudio nltk spacy transformers opencv-python moviepy PyQt6 qt-material requests
fi

# Download required NLTK data
echo "Downloading NLTK data..."
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('vader_lexicon', quiet=True)"

# Download spaCy model
echo "Downloading spaCy model..."
python -m spacy download en_core_web_sm --quiet

# Run the application
echo "Starting application..."
python src/main.py
if [ $? -ne 0 ]; then
    echo "Application exited with an error."
    read -p "Press Enter to exit..."
    exit 1
fi

# Deactivate the virtual environment
deactivate

echo "ClipMaster closed."
read -p "Press Enter to exit..."
