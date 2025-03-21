"""
Video processing service for face tracking, reframing, and adding captions.
"""
import os
import logging
import tempfile
import math
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union
import numpy as np
import cv2
import dlib
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, clips_array

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VideoProcessingService:
    """Service for processing video clips with face tracking, reframing, and captions."""
    
    # Aspect ratio constants
    ASPECT_RATIOS = {
        "9:16": (9, 16),  # Vertical (TikTok, Instagram Stories, YouTube Shorts)
        "1:1": (1, 1),    # Square (Instagram)
        "16:9": (16, 9),  # Horizontal (YouTube, standard video)
    }
    
    def __init__(self):
        """Initialize the video processing service."""
        # Initialize face detector (lazy loading)
        self._face_detector = None
        
        # Initialize face landmark predictor (lazy loading)
        self._landmark_predictor = None
        
        logger.info("Video processing service initialized")
        
    @property
    def face_detector(self):
        """Lazy load face detector."""
        if self._face_detector is None:
            logger.info("Loading face detector...")
            self._face_detector = dlib.get_frontal_face_detector()
        return self._face_detector
        
    @property
    def landmark_predictor(self):
        """Lazy load face landmark predictor."""
        if self._landmark_predictor is None:
            logger.info("Loading face landmark predictor...")
            
            # Define possible locations for the shape predictor file
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "shape_predictor_68_face_landmarks.dat"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "shape_predictor_68_face_landmarks.dat"),
                os.path.join(os.path.expanduser("~"), ".clipmaster", "shape_predictor_68_face_landmarks.dat"),
            ]
            
            # Try to find the file in one of the possible locations
            predictor_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    predictor_path = path
                    break
            
            if predictor_path is None:
                logger.warning("Face landmark predictor not found")
                logger.info("Please download the shape predictor from: "
                           "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2")
                logger.info("Extract it and place it in one of these directories:")
                for path in possible_paths:
                    logger.info(f"- {path}")
                
                # Instead of raising an error, we'll use a fallback method
                logger.info("Face tracking will be disabled. Using center-based tracking instead.")
                return None
                
            logger.info(f"Found face landmark predictor at {predictor_path}")
            self._landmark_predictor = dlib.shape_predictor(predictor_path)
        return self._landmark_predictor
        
    def extract_clip(self, 
                    video_path: str, 
                    start_time: float, 
                    end_time: float, 
                    output_path: Optional[str] = None) -> str:
        """
        Extract a clip from a video.
        
        Args:
            video_path: Path to the video file
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Optional path to save the clip. If not provided, will use a temporary file
            
        Returns:
            str: Path to the extracted clip
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        if output_path is None:
            # Create a temporary file with the same extension as the input video
            ext = os.path.splitext(video_path)[1]
            output_path = tempfile.mktemp(suffix=ext)
            
        logger.info(f"Extracting clip from {start_time}s to {end_time}s")
        
        try:
            # Load the video
            video = VideoFileClip(video_path)
            
            # Extract the clip
            clip = video.subclip(start_time, end_time)
            
            # Write the clip to the output path
            clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
            
            # Close the clips to release resources
            clip.close()
            video.close()
            
            logger.info(f"Clip extracted to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error extracting clip: {e}")
            raise
            
    def reframe_clip(self, 
                    clip_path: str, 
                    aspect_ratio: str = "9:16", 
                    enable_face_tracking: bool = True,
                    output_path: Optional[str] = None) -> str:
        """
        Reframe a video clip to a different aspect ratio with optional face tracking.
        
        Args:
            clip_path: Path to the video clip
            aspect_ratio: Target aspect ratio (9:16, 1:1, or 16:9)
            enable_face_tracking: Whether to enable face tracking
            output_path: Optional path to save the reframed clip. If not provided, will use a temporary file
            
        Returns:
            str: Path to the reframed clip
        """
        if not os.path.exists(clip_path):
            raise FileNotFoundError(f"Clip file not found: {clip_path}")
            
        if aspect_ratio not in self.ASPECT_RATIOS:
            raise ValueError(f"Invalid aspect ratio: {aspect_ratio}. "
                           f"Supported ratios: {list(self.ASPECT_RATIOS.keys())}")
            
        if output_path is None:
            # Create a temporary file with the same extension as the input clip
            ext = os.path.splitext(clip_path)[1]
            output_path = tempfile.mktemp(suffix=ext)
            
        logger.info(f"Reframing clip to aspect ratio: {aspect_ratio}")
        
        try:
            # Load the video clip
            video = VideoFileClip(clip_path)
            
            # Get the original dimensions
            orig_width, orig_height = video.size
            orig_aspect = orig_width / orig_height
            
            # Get the target aspect ratio
            target_width, target_height = self.ASPECT_RATIOS[aspect_ratio]
            target_aspect = target_width / target_height
            
            # Determine the new dimensions
            if target_aspect > orig_aspect:
                # Target is wider than original, crop top and bottom
                new_height = int(orig_width / target_aspect)
                new_width = orig_width
            else:
                # Target is taller than original, crop left and right
                new_width = int(orig_height * target_aspect)
                new_height = orig_height
                
            # If face tracking is enabled, track faces to determine the crop region
            if enable_face_tracking:
                # Track faces throughout the video
                face_positions = self._track_faces(video)
                
                if face_positions:
                    # Calculate the optimal crop region based on face positions
                    crop_x, crop_y = self._calculate_optimal_crop(
                        face_positions, orig_width, orig_height, new_width, new_height
                    )
                else:
                    # If no faces detected, center the crop
                    crop_x = max(0, (orig_width - new_width) // 2)
                    crop_y = max(0, (orig_height - new_height) // 2)
            else:
                # Center the crop
                crop_x = max(0, (orig_width - new_width) // 2)
                crop_y = max(0, (orig_height - new_height) // 2)
                
            # Crop the video
            cropped_clip = video.crop(
                x1=crop_x,
                y1=crop_y,
                width=new_width,
                height=new_height
            )
            
            # Resize to the final dimensions while maintaining the aspect ratio
            final_width = 1080 if target_aspect < 1 else int(1080 * target_aspect)
            final_height = 1080 if target_aspect > 1 else int(1080 / target_aspect)
            
            resized_clip = cropped_clip.resize((final_width, final_height))
            
            # Write the reframed clip to the output path
            resized_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
            
            # Close the clips to release resources
            resized_clip.close()
            cropped_clip.close()
            video.close()
            
            logger.info(f"Clip reframed to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error reframing clip: {e}")
            raise
            
    def _track_faces(self, video: VideoFileClip, sample_rate: int = 10) -> List[Tuple[int, int, int, int]]:
        """
        Track faces throughout a video.
        
        Args:
            video: VideoFileClip object
            sample_rate: Number of frames to sample per second
            
        Returns:
            List[Tuple[int, int, int, int]]: List of face positions (x, y, width, height)
        """
        # Check if face tracking is available
        if self.landmark_predictor is None:
            logger.warning("Face landmark predictor not available. Using center-based tracking.")
            # Return a single "face" at the center of the video
            center_x = video.size[0] // 2
            center_y = video.size[1] // 2
            width = video.size[0] // 3  # Use 1/3 of the video width
            height = video.size[1] // 3  # Use 1/3 of the video height
            return [(center_x - width // 2, center_y - height // 2, width, height)]
            
        face_positions = []
        
        # Calculate the frame interval based on the sample rate
        frame_interval = int(video.fps / sample_rate)
        if frame_interval < 1:
            frame_interval = 1
            
        # Get total number of frames
        total_frames = int(video.fps * video.duration)
        
        logger.info(f"Tracking faces in video with {total_frames} frames, sampling every {frame_interval} frames")
        
        try:
            # Sample frames and detect faces
            for i in range(0, total_frames, frame_interval):
                # Get the frame at the specified time
                time = i / video.fps
                if time > video.duration:
                    break
                    
                frame = video.get_frame(time)
                
                # Convert to grayscale for face detection
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                
                # Detect faces
                faces = self.face_detector(gray)
                
                # If faces are detected, add their positions
                for face in faces:
                    x = face.left()
                    y = face.top()
                    w = face.width()
                    h = face.height()
                    face_positions.append((x, y, w, h))
        except Exception as e:
            logger.error(f"Error during face tracking: {e}")
            logger.warning("Falling back to center-based tracking")
            # Return a single "face" at the center of the video
            center_x = video.size[0] // 2
            center_y = video.size[1] // 2
            width = video.size[0] // 3
            height = video.size[1] // 3
            return [(center_x - width // 2, center_y - height // 2, width, height)]
                
        logger.info(f"Detected {len(face_positions)} face instances in the video")
        
        # If no faces were detected, use the center of the video
        if not face_positions:
            logger.warning("No faces detected. Using center-based tracking.")
            center_x = video.size[0] // 2
            center_y = video.size[1] // 2
            width = video.size[0] // 3
            height = video.size[1] // 3
            return [(center_x - width // 2, center_y - height // 2, width, height)]
            
        return face_positions
        
    def _calculate_optimal_crop(self, 
                              face_positions: List[Tuple[int, int, int, int]], 
                              orig_width: int, 
                              orig_height: int, 
                              crop_width: int, 
                              crop_height: int) -> Tuple[int, int]:
        """
        Calculate the optimal crop region based on face positions.
        
        Args:
            face_positions: List of face positions (x, y, width, height)
            orig_width: Original video width
            orig_height: Original video height
            crop_width: Width of the crop region
            crop_height: Height of the crop region
            
        Returns:
            Tuple[int, int]: Optimal crop position (x, y)
        """
        if not face_positions:
            # If no faces, center the crop
            return max(0, (orig_width - crop_width) // 2), max(0, (orig_height - crop_height) // 2)
            
        # Calculate the average face center
        face_centers = [(x + w // 2, y + h // 2) for x, y, w, h in face_positions]
        avg_x = sum(x for x, _ in face_centers) / len(face_centers)
        avg_y = sum(y for _, y in face_centers) / len(face_centers)
        
        # Calculate the crop position to center the average face
        crop_x = max(0, min(orig_width - crop_width, int(avg_x - crop_width // 2)))
        crop_y = max(0, min(orig_height - crop_height, int(avg_y - crop_height // 2)))
        
        return crop_x, crop_y
        
    def add_captions(self, 
                    clip_path: str, 
                    captions: List[Dict[str, Any]], 
                    font: str = "Arial", 
                    font_size: int = 24,
                    output_path: Optional[str] = None) -> str:
        """
        Add captions to a video clip.
        
        Args:
            clip_path: Path to the video clip
            captions: List of caption dictionaries with text, start_time, and end_time
            font: Font to use for captions
            font_size: Font size for captions
            output_path: Optional path to save the captioned clip. If not provided, will use a temporary file
            
        Returns:
            str: Path to the captioned clip
        """
        if not os.path.exists(clip_path):
            raise FileNotFoundError(f"Clip file not found: {clip_path}")
            
        if output_path is None:
            # Create a temporary file with the same extension as the input clip
            ext = os.path.splitext(clip_path)[1]
            output_path = tempfile.mktemp(suffix=ext)
            
        logger.info(f"Adding captions to clip")
        
        try:
            # Load the video clip
            video = VideoFileClip(clip_path)
            
            # Create text clips for each caption
            text_clips = []
            
            for caption in captions:
                text = caption.get("text", "")
                start_time = caption.get("start_time", 0)
                end_time = caption.get("end_time", 0)
                
                if not text or end_time <= start_time:
                    continue
                    
                # Create a text clip
                txt_clip = TextClip(
                    text,
                    fontsize=font_size,
                    font=font,
                    color='white',
                    stroke_color='black',
                    stroke_width=2,
                    method='caption',
                    size=(video.size[0] * 0.9, None),  # 90% of video width
                    align='center'
                )
                
                # Set position to bottom center with some padding
                txt_clip = txt_clip.set_position(('center', 'bottom')).margin(bottom=20, opacity=0)
                
                # Set the start and end times
                txt_clip = txt_clip.set_start(start_time).set_end(end_time)
                
                text_clips.append(txt_clip)
                
            # Combine the video and text clips
            final_clip = CompositeVideoClip([video] + text_clips)
            
            # Write the captioned clip to the output path
            final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
            
            # Close the clips to release resources
            final_clip.close()
            video.close()
            for clip in text_clips:
                clip.close()
                
            logger.info(f"Captioned clip saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error adding captions: {e}")
            raise
            
    def process_clip(self, 
                    video_path: str, 
                    start_time: float, 
                    end_time: float,
                    captions: List[Dict[str, Any]],
                    aspect_ratio: str = "9:16",
                    enable_face_tracking: bool = True,
                    font: str = "Arial",
                    font_size: int = 24,
                    output_path: Optional[str] = None) -> str:
        """
        Process a video clip with extraction, reframing, and captions.
        
        Args:
            video_path: Path to the original video
            start_time: Start time in seconds
            end_time: End time in seconds
            captions: List of caption dictionaries with text, start_time, and end_time
            aspect_ratio: Target aspect ratio (9:16, 1:1, or 16:9)
            enable_face_tracking: Whether to enable face tracking
            font: Font to use for captions
            font_size: Font size for captions
            output_path: Optional path to save the final clip. If not provided, will use a temporary file
            
        Returns:
            str: Path to the processed clip
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        if output_path is None:
            # Create a temporary file with mp4 extension
            output_path = tempfile.mktemp(suffix=".mp4")
            
        logger.info(f"Processing clip from {start_time}s to {end_time}s")
        
        try:
            # Step 1: Extract the clip
            extracted_path = self.extract_clip(video_path, start_time, end_time)
            
            # Step 2: Reframe the clip
            reframed_path = self.reframe_clip(
                extracted_path, 
                aspect_ratio=aspect_ratio, 
                enable_face_tracking=enable_face_tracking
            )
            
            # Step 3: Add captions
            # Adjust caption timestamps to be relative to the clip
            adjusted_captions = []
            for caption in captions:
                # Skip captions outside the clip timerange
                if caption.get("end_time", 0) <= start_time or caption.get("start_time", 0) >= end_time:
                    continue
                    
                # Adjust timestamps to be relative to the clip
                adjusted_caption = caption.copy()
                adjusted_caption["start_time"] = max(0, caption.get("start_time", 0) - start_time)
                adjusted_caption["end_time"] = min(end_time - start_time, caption.get("end_time", 0) - start_time)
                adjusted_captions.append(adjusted_caption)
                
            final_path = self.add_captions(
                reframed_path,
                adjusted_captions,
                font=font,
                font_size=font_size,
                output_path=output_path
            )
            
            # Clean up temporary files
            if os.path.exists(extracted_path) and extracted_path != video_path:
                os.remove(extracted_path)
                
            if os.path.exists(reframed_path) and reframed_path != final_path:
                os.remove(reframed_path)
                
            logger.info(f"Clip processing complete: {final_path}")
            return final_path
            
        except Exception as e:
            logger.error(f"Error processing clip: {e}")
            raise
