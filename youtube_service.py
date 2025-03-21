"""
YouTube service for downloading and processing YouTube videos.
"""
import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# We'll use yt-dlp for downloading YouTube videos
# It's a fork of youtube-dl with more features and active maintenance
try:
    import yt_dlp as youtube_dl
except ImportError:
    import youtube_dl

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class YouTubeService:
    """Service for downloading and processing YouTube videos."""
    
    def __init__(self, download_dir: str = None):
        """
        Initialize the YouTube service.
        
        Args:
            download_dir: Directory to download videos to. Defaults to a 'downloads' folder in the current directory.
        """
        self.download_dir = download_dir or os.path.join(os.getcwd(), 'downloads')
        os.makedirs(self.download_dir, exist_ok=True)
        logger.info(f"YouTube service initialized with download directory: {self.download_dir}")
        
    def validate_url(self, url: str) -> bool:
        """
        Validate if the given URL is a valid YouTube URL.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if the URL is valid, False otherwise
        """
        youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        match = re.match(youtube_regex, url)
        return match is not None
        
    def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        Get information about a YouTube video.
        
        Args:
            url: YouTube URL
            
        Returns:
            Dict[str, Any]: Dictionary containing video information
        """
        if not self.validate_url(url):
            raise ValueError(f"Invalid YouTube URL: {url}")
            
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'format': 'best',
        }
        
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'description': info.get('description'),
                    'duration': info.get('duration'),
                    'thumbnail': info.get('thumbnail'),
                    'view_count': info.get('view_count'),
                    'like_count': info.get('like_count'),
                    'upload_date': info.get('upload_date'),
                    'uploader': info.get('uploader'),
                    'channel_id': info.get('channel_id'),
                    'formats': info.get('formats'),
                }
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            raise
            
    def download_video(self, url: str, progress_callback=None) -> Tuple[str, Dict[str, Any]]:
        """
        Download a YouTube video.
        
        Args:
            url: YouTube URL
            progress_callback: Optional callback function to report download progress
            
        Returns:
            Tuple[str, Dict[str, Any]]: Tuple containing the path to the downloaded video and video info
        """
        if not self.validate_url(url):
            raise ValueError(f"Invalid YouTube URL: {url}")
            
        # Get video info first to use in the filename
        video_info = self.get_video_info(url)
        video_id = video_info['id']
        video_title = video_info['title']
        
        # Sanitize the title for use in a filename
        safe_title = re.sub(r'[^\w\-_\. ]', '_', video_title)
        output_filename = f"{safe_title}_{video_id}.mp4"
        output_path = os.path.join(self.download_dir, output_filename)
        
        # Define download options
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_path,
            'noplaylist': True,
            'quiet': False,
            'no_warnings': True,
            'progress_hooks': [self._create_progress_hook(progress_callback)] if progress_callback else [],
        }
        
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                logger.info(f"Video downloaded successfully: {output_path}")
                return output_path, video_info
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            raise
            
    def _create_progress_hook(self, callback):
        """
        Create a progress hook for youtube-dl.
        
        Args:
            callback: Callback function to report progress
            
        Returns:
            Function: Progress hook function
        """
        def progress_hook(d):
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '0%')
                speed = d.get('_speed_str', '0KiB/s')
                eta = d.get('_eta_str', '00:00')
                
                # Convert percent string to float (remove % and convert)
                try:
                    percent_float = float(percent.strip('%'))
                except ValueError:
                    percent_float = 0.0
                    
                callback(percent_float, speed, eta)
                
            elif d['status'] == 'finished':
                callback(100.0, '0KiB/s', '00:00')
                logger.info("Download complete, now converting...")
                
        return progress_hook
        
    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> str:
        """
        Extract audio from a video file.
        
        Args:
            video_path: Path to the video file
            output_path: Optional path to save the audio file. If not provided, will use the same name with .mp3 extension
            
        Returns:
            str: Path to the extracted audio file
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        if output_path is None:
            video_dir = os.path.dirname(video_path)
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(video_dir, f"{video_name}.mp3")
            
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"file://{os.path.abspath(video_path)}"])
                logger.info(f"Audio extracted successfully: {output_path}")
                return output_path
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            raise
