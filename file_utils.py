"""
File utility functions for ClipMaster.
"""
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple


def ensure_directory_exists(directory_path: str) -> str:
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        str: Path to the directory
    """
    os.makedirs(directory_path, exist_ok=True)
    return directory_path


def get_temp_directory() -> str:
    """
    Get a temporary directory for the application.
    
    Returns:
        str: Path to the temporary directory
    """
    temp_dir = os.path.join(tempfile.gettempdir(), "clipmaster")
    ensure_directory_exists(temp_dir)
    return temp_dir


def get_app_data_directory() -> str:
    """
    Get the application data directory.
    
    Returns:
        str: Path to the application data directory
    """
    if os.name == 'nt':  # Windows
        app_data = os.path.join(os.environ['APPDATA'], "ClipMaster")
    else:  # macOS/Linux
        app_data = os.path.join(os.path.expanduser("~"), ".clipmaster")
        
    ensure_directory_exists(app_data)
    return app_data


def get_downloads_directory() -> str:
    """
    Get the downloads directory for the application.
    
    Returns:
        str: Path to the downloads directory
    """
    downloads_dir = os.path.join(get_app_data_directory(), "downloads")
    ensure_directory_exists(downloads_dir)
    return downloads_dir


def get_projects_directory() -> str:
    """
    Get the projects directory for the application.
    
    Returns:
        str: Path to the projects directory
    """
    projects_dir = os.path.join(get_app_data_directory(), "projects")
    ensure_directory_exists(projects_dir)
    return projects_dir


def get_exports_directory() -> str:
    """
    Get the exports directory for the application.
    
    Returns:
        str: Path to the exports directory
    """
    exports_dir = os.path.join(get_app_data_directory(), "exports")
    ensure_directory_exists(exports_dir)
    return exports_dir


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        str: Sanitized filename
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[\\/*?:"<>|]', "_", filename)
    
    # Trim whitespace and limit length
    sanitized = sanitized.strip()
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
        
    return sanitized


def get_file_extension(file_path: str) -> str:
    """
    Get the extension of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: File extension (with dot)
    """
    return os.path.splitext(file_path)[1].lower()


def is_video_file(file_path: str) -> bool:
    """
    Check if a file is a video file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        bool: True if the file is a video file, False otherwise
    """
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv']
    return get_file_extension(file_path) in video_extensions


def is_audio_file(file_path: str) -> bool:
    """
    Check if a file is an audio file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        bool: True if the file is an audio file, False otherwise
    """
    audio_extensions = ['.mp3', '.wav', '.ogg', '.aac', '.flac', '.m4a']
    return get_file_extension(file_path) in audio_extensions


def get_file_size(file_path: str) -> int:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        int: File size in bytes
    """
    return os.path.getsize(file_path)


def format_file_size(size_bytes: int) -> str:
    """
    Format a file size in bytes to a human-readable string.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        str: Formatted file size
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def copy_file(source_path: str, destination_path: str) -> str:
    """
    Copy a file from source to destination.
    
    Args:
        source_path: Path to the source file
        destination_path: Path to the destination file
        
    Returns:
        str: Path to the destination file
    """
    shutil.copy2(source_path, destination_path)
    return destination_path


def move_file(source_path: str, destination_path: str) -> str:
    """
    Move a file from source to destination.
    
    Args:
        source_path: Path to the source file
        destination_path: Path to the destination file
        
    Returns:
        str: Path to the destination file
    """
    shutil.move(source_path, destination_path)
    return destination_path


def delete_file(file_path: str) -> bool:
    """
    Delete a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        bool: True if the file was deleted, False otherwise
    """
    try:
        os.remove(file_path)
        return True
    except (OSError, FileNotFoundError):
        return False


def list_files_by_extension(directory_path: str, extensions: List[str]) -> List[str]:
    """
    List files in a directory with specific extensions.
    
    Args:
        directory_path: Path to the directory
        extensions: List of file extensions to include (with dot)
        
    Returns:
        List[str]: List of file paths
    """
    files = []
    for root, _, filenames in os.walk(directory_path):
        for filename in filenames:
            if any(filename.lower().endswith(ext.lower()) for ext in extensions):
                files.append(os.path.join(root, filename))
    return files


def list_video_files(directory_path: str) -> List[str]:
    """
    List video files in a directory.
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        List[str]: List of video file paths
    """
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv']
    return list_files_by_extension(directory_path, video_extensions)


def list_audio_files(directory_path: str) -> List[str]:
    """
    List audio files in a directory.
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        List[str]: List of audio file paths
    """
    audio_extensions = ['.mp3', '.wav', '.ogg', '.aac', '.flac', '.m4a']
    return list_files_by_extension(directory_path, audio_extensions)


def get_video_duration(file_path: str) -> Optional[float]:
    """
    Get the duration of a video file in seconds.
    
    Args:
        file_path: Path to the video file
        
    Returns:
        Optional[float]: Duration in seconds, or None if the duration could not be determined
    """
    try:
        from moviepy.editor import VideoFileClip
        with VideoFileClip(file_path) as video:
            return video.duration
    except Exception:
        return None


def format_time(seconds: float) -> str:
    """
    Format time in seconds to a string (HH:MM:SS).
    
    Args:
        seconds: Time in seconds
        
    Returns:
        str: Formatted time
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"
