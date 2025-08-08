from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionResult:
    """Represents a transcription result with confidence scoring"""
    
    text: str
    service: str
    confidence: float
    language_code: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate the transcription result"""
        if not self.text or not self.text.strip():
            raise ValueError("Transcription text cannot be empty")
        
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        
        if not self.service:
            raise ValueError("Service name cannot be empty")
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if the transcription has high confidence"""
        return self.confidence >= threshold
    
    def is_medium_confidence(self, low_threshold: float = 0.6, high_threshold: float = 0.8) -> bool:
        """Check if the transcription has medium confidence"""
        return low_threshold <= self.confidence < high_threshold
    
    def is_low_confidence(self, threshold: float = 0.6) -> bool:
        """Check if the transcription has low confidence"""
        return self.confidence < threshold
    
    def get_confidence_level(self) -> str:
        """Get human-readable confidence level"""
        if self.is_high_confidence():
            return "high"
        elif self.is_medium_confidence():
            return "medium"
        else:
            return "low"
    
    def __str__(self) -> str:
        return f"TranscriptionResult(text='{self.text[:50]}...', service={self.service}, confidence={self.confidence:.3f})"
    
    def __repr__(self) -> str:
        return self.__str__()


class TranscriptionQualityAnalyzer:
    """Analyzes transcription quality and provides confidence scoring"""
    
    @staticmethod
    def calculate_text_quality_score(text: str) -> float:
        """Calculate a quality score based on text characteristics"""
        if not text or not text.strip():
            return 0.0
        
        score = 1.0
        
        # Penalize very short texts (likely incomplete)
        if len(text.strip()) < 3:
            score -= 0.3
        
        # Penalize texts with too many repeated characters (likely noise)
        import re
        repeated_chars = re.findall(r'(.)\1{2,}', text)
        if repeated_chars:
            score -= min(0.2, len(repeated_chars) * 0.05)
        
        # Penalize texts with too many special characters
        special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s.,!?]', text)) / len(text)
        if special_char_ratio > 0.3:
            score -= 0.2
        
        # Bonus for proper sentence structure
        if text.strip().endswith(('.', '!', '?')):
            score += 0.1
        
        # Bonus for reasonable length (not too short, not too long)
        word_count = len(text.split())
        if 2 <= word_count <= 50:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def compare_transcriptions(results: list[TranscriptionResult]) -> TranscriptionResult:
        """Compare multiple transcription results and return the best one"""
        if not results:
            raise ValueError("No transcription results to compare")
        
        # Sort by confidence score (highest first)
        sorted_results = sorted(results, key=lambda x: x.confidence, reverse=True)
        
        # If the highest confidence is significantly better, use it
        if len(sorted_results) > 1:
            confidence_diff = sorted_results[0].confidence - sorted_results[1].confidence
            if confidence_diff > 0.1:  # 10% difference threshold
                logger.info(f"Using {sorted_results[0].service} (confidence: {sorted_results[0].confidence:.3f}) "
                          f"over {sorted_results[1].service} (confidence: {sorted_results[1].confidence:.3f})")
                return sorted_results[0]
        
        # If confidences are close, prefer Whisper for Hebrew and other languages
        for result in sorted_results:
            if result.service == 'whisper':
                logger.info(f"Using Whisper despite similar confidence due to better language support")
                return result
        
        # Default to highest confidence
        return sorted_results[0]
