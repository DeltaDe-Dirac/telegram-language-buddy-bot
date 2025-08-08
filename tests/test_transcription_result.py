import pytest
from src.models.transcription_result import TranscriptionResult, TranscriptionQualityAnalyzer


class TestTranscriptionResult:
    """Test TranscriptionResult class"""
    
    def test_transcription_result_creation(self):
        """Test creating a TranscriptionResult"""
        result = TranscriptionResult(
            text="Hello world",
            service="whisper",
            confidence=0.9
        )
        
        assert result.text == "Hello world"
        assert result.service == "whisper"
        assert result.confidence == 0.9
        assert result.language_code is None
        assert result.raw_response is None
    
    def test_transcription_result_validation(self):
        """Test TranscriptionResult validation"""
        # Test empty text
        with pytest.raises(ValueError, match="Transcription text cannot be empty"):
            TranscriptionResult(text="", service="whisper", confidence=0.9)
        
        # Test invalid confidence
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            TranscriptionResult(text="Hello", service="whisper", confidence=1.5)
        
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            TranscriptionResult(text="Hello", service="whisper", confidence=-0.1)
        
        # Test empty service
        with pytest.raises(ValueError, match="Service name cannot be empty"):
            TranscriptionResult(text="Hello", service="", confidence=0.9)
    
    def test_confidence_levels(self):
        """Test confidence level methods"""
        high_result = TranscriptionResult(text="Hello", service="whisper", confidence=0.9)
        medium_result = TranscriptionResult(text="Hello", service="whisper", confidence=0.7)
        low_result = TranscriptionResult(text="Hello", service="whisper", confidence=0.4)
        
        assert high_result.is_high_confidence()
        assert not high_result.is_medium_confidence()
        assert not high_result.is_low_confidence()
        assert high_result.get_confidence_level() == "high"
        
        assert not medium_result.is_high_confidence()
        assert medium_result.is_medium_confidence()
        assert not medium_result.is_low_confidence()
        assert medium_result.get_confidence_level() == "medium"
        
        assert not low_result.is_high_confidence()
        assert not low_result.is_medium_confidence()
        assert low_result.is_low_confidence()
        assert low_result.get_confidence_level() == "low"
    
    def test_string_representation(self):
        """Test string representation"""
        result = TranscriptionResult(text="Hello world", service="whisper", confidence=0.9)
        str_repr = str(result)
        
        assert "Hello world" in str_repr
        assert "whisper" in str_repr
        assert "0.900" in str_repr


class TestTranscriptionQualityAnalyzer:
    """Test TranscriptionQualityAnalyzer class"""
    
    def test_calculate_text_quality_score_empty(self):
        """Test quality score calculation for empty text"""
        score = TranscriptionQualityAnalyzer.calculate_text_quality_score("")
        assert score == 0.0
        
        score = TranscriptionQualityAnalyzer.calculate_text_quality_score("   ")
        assert score == 0.0
    
    def test_calculate_text_quality_score_short(self):
        """Test quality score calculation for short text"""
        score = TranscriptionQualityAnalyzer.calculate_text_quality_score("Hi")
        assert score < 1.0  # Should be penalized for being too short
    
    def test_calculate_text_quality_score_good(self):
        """Test quality score calculation for good text"""
        score = TranscriptionQualityAnalyzer.calculate_text_quality_score("Hello world!")
        assert score > 0.8  # Should have good score
    
    def test_calculate_text_quality_score_repeated_chars(self):
        """Test quality score calculation for text with repeated characters"""
        score = TranscriptionQualityAnalyzer.calculate_text_quality_score("Helllllo world")
        assert 0.0 <= score <= 1.0  # Should be a valid score
    
    def test_calculate_text_quality_score_special_chars(self):
        """Test quality score calculation for text with special characters"""
        score = TranscriptionQualityAnalyzer.calculate_text_quality_score("Hello @#$% world")
        assert 0.0 <= score <= 1.0  # Should be a valid score
    
    def test_compare_transcriptions_single(self):
        """Test comparing single transcription"""
        result = TranscriptionResult(text="Hello", service="whisper", confidence=0.9)
        best = TranscriptionQualityAnalyzer.compare_transcriptions([result])
        assert best == result
    
    def test_compare_transcriptions_multiple(self):
        """Test comparing multiple transcriptions"""
        whisper_result = TranscriptionResult(text="Hello", service="whisper", confidence=0.8)
        assembly_result = TranscriptionResult(text="Hello", service="assemblyai", confidence=0.9)
        
        best = TranscriptionQualityAnalyzer.compare_transcriptions([whisper_result, assembly_result])
        # With 0.1 difference (exactly at threshold), Whisper is preferred due to better language support
        assert best == whisper_result  # Whisper preferred when confidences are close
    
    def test_compare_transcriptions_whisper_preference(self):
        """Test that Whisper is preferred when confidences are close"""
        whisper_result = TranscriptionResult(text="Hello", service="whisper", confidence=0.8)
        assembly_result = TranscriptionResult(text="Hello", service="assemblyai", confidence=0.81)
        
        best = TranscriptionQualityAnalyzer.compare_transcriptions([whisper_result, assembly_result])
        assert best == whisper_result  # Whisper preferred despite slightly lower confidence
    
    def test_compare_transcriptions_empty_list(self):
        """Test comparing empty list"""
        with pytest.raises(ValueError, match="No transcription results to compare"):
            TranscriptionQualityAnalyzer.compare_transcriptions([])
