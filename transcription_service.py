"""
Transcription service for converting audio to text.
"""
import os
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Import whisper for transcription
import whisper
import torch

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for transcribing audio to text."""
    
    # Available whisper models
    AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large"]
    
    def __init__(self, model_name: str = "base", device: str = None):
        """
        Initialize the transcription service.
        
        Args:
            model_name: Name of the whisper model to use. Options: tiny, base, small, medium, large
            device: Device to use for inference. If None, will use CUDA if available, otherwise CPU
        """
        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model name: {model_name}. Available models: {self.AVAILABLE_MODELS}")
            
        self.model_name = model_name
        
        # Determine device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Initializing transcription service with model: {model_name} on device: {self.device}")
        
        # Load the model (lazy loading - will be loaded on first use)
        self._model = None
        
    @property
    def model(self):
        """Lazy load the model on first use."""
        if self._model is None:
            logger.info(f"Loading whisper model: {self.model_name}")
            self._model = whisper.load_model(self.model_name, device=self.device)
        return self._model
        
    def transcribe(self, audio_path: str, language: str = None, progress_callback=None) -> Dict[str, Any]:
        """
        Transcribe an audio file to text.
        
        Args:
            audio_path: Path to the audio file
            language: Optional language code (e.g., 'en', 'es'). If None, will auto-detect
            progress_callback: Optional callback function to report transcription progress
            
        Returns:
            Dict[str, Any]: Dictionary containing transcription results
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        logger.info(f"Transcribing audio file: {audio_path}")
        
        # Report initial progress
        if progress_callback:
            progress_callback(0, "Loading model...")
            
        # Load the model if not already loaded
        model = self.model
        
        # Report progress
        if progress_callback:
            progress_callback(10, "Model loaded, starting transcription...")
            
        # Set transcription options
        options = {}
        if language:
            options["language"] = language
            
        try:
            # Perform transcription
            result = model.transcribe(audio_path, **options)
            
            # Report completion
            if progress_callback:
                progress_callback(100, "Transcription complete")
                
            logger.info(f"Transcription complete for: {audio_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise
            
    def transcribe_with_timestamps(self, audio_path: str, language: str = None) -> List[Dict[str, Any]]:
        """
        Transcribe an audio file with timestamps for each segment.
        
        Args:
            audio_path: Path to the audio file
            language: Optional language code (e.g., 'en', 'es'). If None, will auto-detect
            
        Returns:
            List[Dict[str, Any]]: List of segments with text and timestamps
        """
        result = self.transcribe(audio_path, language)
        return result.get("segments", [])
        
    def save_transcription(self, transcription: Dict[str, Any], output_path: str) -> str:
        """
        Save transcription to a file.
        
        Args:
            transcription: Transcription result from transcribe method
            output_path: Path to save the transcription
            
        Returns:
            str: Path to the saved transcription file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(transcription.get("text", ""))
                
            logger.info(f"Transcription saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving transcription: {e}")
            raise
            
    def save_transcription_with_timestamps(self, segments: List[Dict[str, Any]], output_path: str) -> str:
        """
        Save transcription with timestamps to a file.
        
        Args:
            segments: List of segments from transcribe_with_timestamps method
            output_path: Path to save the transcription
            
        Returns:
            str: Path to the saved transcription file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for segment in segments:
                    start = segment.get("start", 0)
                    end = segment.get("end", 0)
                    text = segment.get("text", "")
                    
                    # Format timestamps as [HH:MM:SS.mmm]
                    start_formatted = self._format_timestamp(start)
                    end_formatted = self._format_timestamp(end)
                    
                    f.write(f"[{start_formatted} --> {end_formatted}] {text}\n")
                    
            logger.info(f"Timestamped transcription saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving timestamped transcription: {e}")
            raise
            
    def _format_timestamp(self, seconds: float) -> str:
        """
        Format seconds as HH:MM:SS.mmm.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            str: Formatted timestamp
        """
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
        
    def get_word_timestamps(self, audio_path: str, language: str = None) -> List[Dict[str, Any]]:
        """
        Get timestamps for each word in the audio.
        
        Args:
            audio_path: Path to the audio file
            language: Optional language code (e.g., 'en', 'es'). If None, will auto-detect
            
        Returns:
            List[Dict[str, Any]]: List of words with timestamps
        """
        # Set transcription options
        options = {
            "word_timestamps": True,  # Enable word timestamps
        }
        
        if language:
            options["language"] = language
            
        try:
            # Perform transcription with word timestamps
            result = self.model.transcribe(audio_path, **options)
            
            # Extract words with timestamps
            words = []
            for segment in result.get("segments", []):
                for word in segment.get("words", []):
                    words.append({
                        "word": word.get("word"),
                        "start": word.get("start"),
                        "end": word.get("end"),
                        "confidence": word.get("confidence", 1.0),
                    })
                    
            return words
            
        except Exception as e:
            logger.error(f"Error getting word timestamps: {e}")
            raise
