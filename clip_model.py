"""
Model for storing clip data.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import json
import os


@dataclass
class Caption:
    """Caption model for storing caption data."""
    text: str
    start_time: float
    end_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Caption':
        """Create from dictionary."""
        return cls(
            text=data.get("text", ""),
            start_time=data.get("start_time", 0.0),
            end_time=data.get("end_time", 0.0),
        )


@dataclass
class Clip:
    """Clip model for storing clip data."""
    start_time: float
    end_time: float
    duration: float
    score: float = 0.0
    text: str = ""
    captions: List[Caption] = field(default_factory=list)
    video_path: Optional[str] = None
    processed_path: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "score": self.score,
            "text": self.text,
            "captions": [caption.to_dict() for caption in self.captions],
            "video_path": self.video_path,
            "processed_path": self.processed_path,
            "details": self.details,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Clip':
        """Create from dictionary."""
        captions = [Caption.from_dict(caption) for caption in data.get("captions", [])]
        return cls(
            start_time=data.get("start_time", 0.0),
            end_time=data.get("end_time", 0.0),
            duration=data.get("duration", 0.0),
            score=data.get("score", 0.0),
            text=data.get("text", ""),
            captions=captions,
            video_path=data.get("video_path"),
            processed_path=data.get("processed_path"),
            details=data.get("details", {}),
        )


@dataclass
class Project:
    """Project model for storing project data."""
    name: str
    video_path: str
    clips: List[Clip] = field(default_factory=list)
    transcription: Optional[str] = None
    transcription_segments: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "video_path": self.video_path,
            "clips": [clip.to_dict() for clip in self.clips],
            "transcription": self.transcription,
            "transcription_segments": self.transcription_segments,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create from dictionary."""
        clips = [Clip.from_dict(clip) for clip in data.get("clips", [])]
        return cls(
            name=data.get("name", ""),
            video_path=data.get("video_path", ""),
            clips=clips,
            transcription=data.get("transcription"),
            transcription_segments=data.get("transcription_segments", []),
        )
        
    def save(self, file_path: str) -> str:
        """Save project to file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
        return file_path
        
    @classmethod
    def load(cls, file_path: str) -> 'Project':
        """Load project from file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Project file not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        return cls.from_dict(data)
