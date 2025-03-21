"""
Clip detection service for finding viral-worthy segments in videos.
"""
import os
import logging
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

# NLP libraries
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import spacy
from transformers import pipeline

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ClipDetectionService:
    """Service for detecting viral-worthy clips in videos based on transcription."""
    
    def __init__(self):
        """Initialize the clip detection service."""
        # Ensure NLTK resources are downloaded
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            logger.info("Downloading NLTK punkt tokenizer...")
            nltk.download('punkt', quiet=True)
            
        try:
            nltk.data.find('sentiment/vader_lexicon.zip')
        except LookupError:
            logger.info("Downloading NLTK vader lexicon...")
            nltk.download('vader_lexicon', quiet=True)
        
        # Initialize sentiment analyzer
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        # Initialize spaCy for NLP tasks (lazy loading)
        self._nlp = None
        
        # Initialize emotion detection (lazy loading)
        self._emotion_detector = None
        
        logger.info("Clip detection service initialized")
        
    @property
    def nlp(self):
        """Lazy load spaCy model."""
        if self._nlp is None:
            logger.info("Loading spaCy model...")
            try:
                self._nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.info("Downloading spaCy model...")
                spacy.cli.download("en_core_web_sm")
                self._nlp = spacy.load("en_core_web_sm")
        return self._nlp
        
    @property
    def emotion_detector(self):
        """Lazy load emotion detection model."""
        if self._emotion_detector is None:
            logger.info("Loading emotion detection model...")
            self._emotion_detector = pipeline("text-classification", 
                                             model="j-hartmann/emotion-english-distilroberta-base", 
                                             top_k=None)
        return self._emotion_detector
        
    def detect_clips(self, 
                    transcription_segments: List[Dict[str, Any]], 
                    target_duration: int = 60,
                    min_duration: int = 30,
                    max_duration: int = 90,
                    max_clips: int = 5) -> List[Dict[str, Any]]:
        """
        Detect viral-worthy clips from transcription segments.
        
        Args:
            transcription_segments: List of transcription segments with timestamps
            target_duration: Target duration for clips in seconds
            min_duration: Minimum duration for clips in seconds
            max_duration: Maximum duration for clips in seconds
            max_clips: Maximum number of clips to return
            
        Returns:
            List[Dict[str, Any]]: List of detected clips with start/end times and scores
        """
        if not transcription_segments:
            logger.warning("No transcription segments provided")
            return []
            
        logger.info(f"Detecting clips with target duration: {target_duration}s")
        
        # Calculate features for each segment
        segments_with_features = self._calculate_segment_features(transcription_segments)
        
        # Find potential clip boundaries
        potential_clips = self._find_potential_clips(segments_with_features, 
                                                   target_duration, 
                                                   min_duration, 
                                                   max_duration)
        
        # Score and rank clips
        scored_clips = self._score_clips(potential_clips)
        
        # Sort by score (descending) and take top N
        top_clips = sorted(scored_clips, key=lambda x: x["score"], reverse=True)[:max_clips]
        
        logger.info(f"Detected {len(top_clips)} clips")
        return top_clips
        
    def _calculate_segment_features(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate features for each transcription segment.
        
        Args:
            segments: List of transcription segments
            
        Returns:
            List[Dict[str, Any]]: Segments with added features
        """
        result = []
        
        for segment in segments:
            text = segment.get("text", "").strip()
            if not text:
                continue
                
            # Basic segment info
            segment_with_features = {
                "start": segment.get("start", 0),
                "end": segment.get("end", 0),
                "text": text,
                "duration": segment.get("end", 0) - segment.get("start", 0),
            }
            
            # Calculate sentiment
            sentiment = self.sentiment_analyzer.polarity_scores(text)
            segment_with_features["sentiment"] = sentiment
            
            # Calculate emotion
            emotions = self._detect_emotion(text)
            segment_with_features["emotions"] = emotions
            
            # Calculate linguistic features
            doc = self.nlp(text)
            
            # Check for questions
            segment_with_features["is_question"] = any(sent.text.endswith("?") for sent in doc.sents)
            
            # Check for exclamations
            segment_with_features["is_exclamation"] = any(sent.text.endswith("!") for sent in doc.sents)
            
            # Count named entities
            segment_with_features["named_entities"] = len(doc.ents)
            
            # Check for keywords indicating viral content
            viral_keywords = ["amazing", "incredible", "unbelievable", "shocking", "surprising", 
                             "never", "ever", "best", "worst", "secret", "trick", "hack", 
                             "revealed", "exclusive", "breaking"]
            segment_with_features["viral_keyword_count"] = sum(1 for word in text.lower().split() 
                                                             if word in viral_keywords)
            
            result.append(segment_with_features)
            
        return result
        
    def _detect_emotion(self, text: str) -> Dict[str, float]:
        """
        Detect emotions in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict[str, float]: Dictionary of emotion scores
        """
        try:
            results = self.emotion_detector(text)
            # Convert to dictionary format {emotion: score}
            emotions = {item["label"]: item["score"] for item in results[0]}
            return emotions
        except Exception as e:
            logger.error(f"Error detecting emotions: {e}")
            # Return empty emotions if there's an error
            return {}
            
    def _find_potential_clips(self, 
                             segments: List[Dict[str, Any]], 
                             target_duration: int,
                             min_duration: int,
                             max_duration: int) -> List[Dict[str, Any]]:
        """
        Find potential clips by combining segments.
        
        Args:
            segments: List of segments with features
            target_duration: Target duration for clips in seconds
            min_duration: Minimum duration for clips in seconds
            max_duration: Maximum duration for clips in seconds
            
        Returns:
            List[Dict[str, Any]]: List of potential clips
        """
        potential_clips = []
        
        # Try different starting points
        for start_idx in range(len(segments)):
            current_duration = 0
            end_idx = start_idx
            
            # Add segments until we reach or exceed the target duration
            while end_idx < len(segments) and current_duration < max_duration:
                current_duration += segments[end_idx]["duration"]
                
                # If we've reached minimum duration, this is a potential clip
                if min_duration <= current_duration <= max_duration:
                    clip = {
                        "start_time": segments[start_idx]["start"],
                        "end_time": segments[end_idx]["end"],
                        "duration": current_duration,
                        "segments": segments[start_idx:end_idx+1],
                    }
                    potential_clips.append(clip)
                    
                    # If we're very close to target duration, break
                    if abs(current_duration - target_duration) < 5:
                        break
                        
                end_idx += 1
                
        return potential_clips
        
    def _score_clips(self, clips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score clips based on their viral potential.
        
        Args:
            clips: List of potential clips
            
        Returns:
            List[Dict[str, Any]]: Clips with scores
        """
        scored_clips = []
        
        for clip in clips:
            segments = clip["segments"]
            
            # Initialize scores
            sentiment_score = 0
            emotion_score = 0
            question_score = 0
            exclamation_score = 0
            entity_score = 0
            keyword_score = 0
            
            # Calculate scores based on segments
            for segment in segments:
                # Sentiment score - we want high absolute sentiment (very positive or very negative)
                sentiment = segment["sentiment"]
                sentiment_score += abs(sentiment["compound"]) * segment["duration"]
                
                # Emotion score - we want high emotion intensity
                emotions = segment.get("emotions", {})
                if emotions:
                    # Prioritize joy, surprise, anger as they tend to be more viral
                    emotion_intensity = emotions.get("joy", 0) * 1.5 + \
                                       emotions.get("surprise", 0) * 1.3 + \
                                       emotions.get("anger", 0) * 1.2 + \
                                       emotions.get("fear", 0) + \
                                       emotions.get("sadness", 0) + \
                                       emotions.get("disgust", 0)
                    emotion_score += emotion_intensity * segment["duration"]
                
                # Question and exclamation score
                if segment["is_question"]:
                    question_score += segment["duration"]
                if segment["is_exclamation"]:
                    exclamation_score += segment["duration"]
                    
                # Entity score - more named entities can indicate more informative content
                entity_score += segment["named_entities"] * segment["duration"]
                
                # Keyword score - viral keywords
                keyword_score += segment["viral_keyword_count"] * segment["duration"]
            
            # Normalize scores by clip duration
            clip_duration = clip["duration"]
            sentiment_score /= clip_duration
            emotion_score /= clip_duration
            question_score /= clip_duration
            exclamation_score /= clip_duration
            entity_score /= clip_duration
            keyword_score /= clip_duration
            
            # Calculate final score with weights
            final_score = (
                sentiment_score * 0.2 +
                emotion_score * 0.3 +
                question_score * 0.15 +
                exclamation_score * 0.15 +
                entity_score * 0.1 +
                keyword_score * 0.1
            )
            
            # Duration penalty - prefer clips closer to target duration
            duration_diff = abs(clip["duration"] - 60)  # Assuming 60s is ideal
            duration_penalty = max(0, 1 - (duration_diff / 30))  # Max 30s difference
            
            # Apply duration penalty
            final_score *= duration_penalty
            
            # Create scored clip
            scored_clip = {
                "start_time": clip["start_time"],
                "end_time": clip["end_time"],
                "duration": clip["duration"],
                "score": final_score,
                "text": " ".join(segment["text"] for segment in segments),
                "details": {
                    "sentiment_score": sentiment_score,
                    "emotion_score": emotion_score,
                    "question_score": question_score,
                    "exclamation_score": exclamation_score,
                    "entity_score": entity_score,
                    "keyword_score": keyword_score,
                }
            }
            
            scored_clips.append(scored_clip)
            
        return scored_clips
        
    def save_clips_to_file(self, clips: List[Dict[str, Any]], output_path: str) -> str:
        """
        Save detected clips to a JSON file.
        
        Args:
            clips: List of detected clips
            output_path: Path to save the clips
            
        Returns:
            str: Path to the saved file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(clips, f, indent=2)
                
            logger.info(f"Clips saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving clips: {e}")
            raise
