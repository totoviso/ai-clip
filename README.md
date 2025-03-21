# ClipMaster

A sleek, modern, self-hosted video clipping software designed for commercial use. ClipMaster allows you to input a YouTube URL, automatically transcribe the video, find viral clip segments from the transcription, and reframe the selected parts into short, engaging clips with face tracking and captions.

## Features

- **YouTube Integration**: Input a YouTube URL and automatically download the video for processing
- **Automatic Transcription**: Convert speech to text using advanced AI models
- **Viral Clip Detection**: Use NLP to analyze the transcript and identify viral-worthy segments
- **Reframing & Face Tracking**: Automatically reframe clips to fit different aspect ratios with intelligent face tracking
- **Captions Generation**: Add customizable captions to your clips
- **Modern GUI**: Clean, intuitive interface for easy clip creation and editing
- **Commercial Use**: Designed for commercial applications with batch processing capabilities

## Requirements

- Python 3.8 or higher
- Windows, macOS, or Linux operating system
- Internet connection for YouTube downloads and some AI features
- GPU recommended for faster processing (but not required)

### Prerequisites

Some dependencies require additional system packages:

- **Windows users**:
  - Visual C++ Build Tools (for some packages that might need compilation)
  - If you encounter issues with dlib installation, install CMake from [cmake.org](https://cmake.org/download/)

- **macOS users**:
  - Xcode Command Line Tools: `xcode-select --install`
  - Homebrew: [brew.sh](https://brew.sh/)
  - CMake: `brew install cmake`

- **Linux users**:
  - Build essentials: `sudo apt install build-essential` (Ubuntu/Debian) or `sudo yum groupinstall "Development Tools"` (CentOS/RHEL)
  - CMake: `sudo apt install cmake` (Ubuntu/Debian) or `sudo yum install cmake` (CentOS/RHEL)

## Installation

1. Clone or download this repository
2. Run the `run_clipmaster.bat` file (Windows) or `./run_clipmaster.sh` (macOS/Linux)
3. The application will automatically set up a virtual environment and install all required dependencies

### Manual Installation

If you encounter issues with the automatic installation:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

### Troubleshooting

- **dlib installation issues**: If you encounter problems installing dlib, make sure CMake is installed and in your PATH. For Windows users, we use a pre-built wheel (dlib-bin) to avoid compilation issues.
- **Face tracking**: Download the shape predictor file from [dlib.net](http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2), extract it, and place it in the `src/backend/services` directory.

## Usage

1. Launch ClipMaster using the batch file or by running `python src/main.py`
2. Enter a YouTube URL in the input field
3. Click "Download & Process" to download the video and prepare it for processing
4. Navigate through the tabs to:
   - View the downloaded video
   - Generate and edit the transcription
   - Detect viral-worthy clips
   - Edit clips with different aspect ratios and face tracking
   - Export the final clips in your desired format

## Advanced Features

### Transcription Options

- Multiple language support
- Manual editing capabilities for corrections
- Timestamp-based navigation

### Clip Detection

- Customizable clip length (30-90 seconds)
- Emotion and sentiment analysis
- Keyword-based detection

### Editing Options

- Multiple aspect ratios (9:16, 1:1, 16:9)
- Face tracking to keep subjects centered
- Custom caption styling (font, size, color)

### Export Options

- Multiple resolutions (1080p, 720p, etc.)
- Various formats (MP4, MOV, WebM)
- Batch export capabilities

## Technical Details

ClipMaster is built using:

- **Python**: Core application logic
- **PyQt6**: Modern GUI framework
- **yt-dlp**: YouTube video downloading
- **Whisper**: State-of-the-art speech recognition
- **NLTK/spaCy**: Natural language processing for clip detection
- **OpenCV/dlib**: Computer vision for face tracking
- **MoviePy**: Video processing and editing

## License

This software is intended for commercial use. Please contact the developers for licensing information.

## Disclaimer

When using YouTube content, ensure you comply with YouTube's Terms of Service and copyright laws. This software is designed to help create clips within fair use guidelines, but users are responsible for ensuring their usage complies with all applicable laws and terms of service.
