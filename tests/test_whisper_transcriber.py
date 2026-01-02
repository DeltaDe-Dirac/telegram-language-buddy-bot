import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import tempfile
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models.whisper_transcriber import WhisperTranscriber


class TestWhisperTranscriber(unittest.TestCase):
    """Test cases for WhisperTranscriber class"""

    def setUp(self):
        """Set up test fixtures"""
        # Clear environment variables for consistent testing
        self.original_key = os.environ.get('OPENAI_API_KEY')
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']

    def tearDown(self):
        """Clean up test fixtures"""
        # Restore original environment
        if self.original_key:
            os.environ['OPENAI_API_KEY'] = self.original_key
        elif 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']

    def test_initialization_with_api_key(self):
        """Test initialization with valid API key"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key_123'}):
            transcriber = WhisperTranscriber()
            self.assertTrue(transcriber.available)
            self.assertEqual(transcriber.api_key, 'test_key_123')
            self.assertEqual(transcriber.base_url, "https://api.openai.com/v1/audio/transcriptions")

    def test_initialization_without_api_key(self):
        """Test initialization without API key"""
        transcriber = WhisperTranscriber()
        self.assertFalse(transcriber.available)
        self.assertEqual(transcriber.api_key, '')
        self.assertEqual(transcriber.base_url, "https://api.openai.com/v1/audio/transcriptions")

    def test_initialization_api_key_with_quotes(self):
        """Test initialization with API key containing quotes"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': '"test_key_123"'}):
            transcriber = WhisperTranscriber()
            self.assertTrue(transcriber.available)
            self.assertEqual(transcriber.api_key, 'test_key_123')

    def test_initialization_api_key_with_whitespace(self):
        """Test initialization with API key containing whitespace"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': '  test_key_123  '}):
            transcriber = WhisperTranscriber()
            self.assertTrue(transcriber.available)
            self.assertEqual(transcriber.api_key, 'test_key_123')

    def test_transcribe_audio_not_available(self):
        """Test transcription when service is not available"""
        transcriber = WhisperTranscriber()
        self.assertFalse(transcriber.available)

        result = transcriber.transcribe_audio("dummy_path.mp3")
        self.assertIsNone(result)

    @patch('models.whisper_transcriber.requests.post')
    def test_transcribe_audio_success(self, mock_post):
        """Test successful audio transcription"""
        # Create a temporary audio file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(b'dummy audio content')
            temp_path = temp_file.name

        try:
            # Mock successful API response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'text': 'Hello world transcript'}
            mock_post.return_value = mock_response

            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
                transcriber = WhisperTranscriber()
                result = transcriber.transcribe_audio(temp_path)

                # Verify result
                self.assertIsNotNone(result)
                self.assertEqual(result.text, 'Hello world transcript')
                self.assertEqual(result.service, 'whisper')
                self.assertGreater(result.confidence, 0)

                # Verify API call
                mock_post.assert_called_once()
                call_args = mock_post.call_args
                self.assertEqual(call_args[0][0], "https://api.openai.com/v1/audio/transcriptions")
                self.assertIn('Authorization', call_args[1]['headers'])
                self.assertEqual(call_args[1]['headers']['Authorization'], 'Bearer test_key')

        finally:
            os.unlink(temp_path)

    @patch('models.whisper_transcriber.requests.post')
    def test_transcribe_audio_empty_response(self, mock_post):
        """Test transcription with empty response text"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(b'dummy audio content')
            temp_path = temp_file.name

        try:
            # Mock response with empty text
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'text': ''}
            mock_post.return_value = mock_response

            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
                transcriber = WhisperTranscriber()
                result = transcriber.transcribe_audio(temp_path)

                # Should return None for empty transcript
                self.assertIsNone(result)

        finally:
            os.unlink(temp_path)

    @patch('models.whisper_transcriber.requests.post')
    def test_transcribe_audio_whitespace_only_response(self, mock_post):
        """Test transcription with whitespace-only response"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(b'dummy audio content')
            temp_path = temp_file.name

        try:
            # Mock response with whitespace-only text
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'text': '   \n\t  '}
            mock_post.return_value = mock_response

            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
                transcriber = WhisperTranscriber()
                result = transcriber.transcribe_audio(temp_path)

                # Should return None for whitespace-only transcript
                self.assertIsNone(result)

        finally:
            os.unlink(temp_path)

    @patch('models.whisper_transcriber.requests.post')
    def test_transcribe_audio_403_model_not_found(self, mock_post):
        """Test transcription with 403 model not found error"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(b'dummy audio content')
            temp_path = temp_file.name

        try:
            # Mock 403 response with model_not_found error
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.json.return_value = {'error': {'code': 'model_not_found'}}
            mock_post.return_value = mock_response

            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
                transcriber = WhisperTranscriber()
                self.assertTrue(transcriber.available)  # Initially available

                result = transcriber.transcribe_audio(temp_path)

                # Should return None and disable service
                self.assertIsNone(result)
                self.assertFalse(transcriber.available)  # Service should be disabled

        finally:
            os.unlink(temp_path)

    @patch('models.whisper_transcriber.requests.post')
    def test_transcribe_audio_403_other_error(self, mock_post):
        """Test transcription with 403 error (not model not found)"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(b'dummy audio content')
            temp_path = temp_file.name

        try:
            # Mock 403 response with other error
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.json.return_value = {'error': {'code': 'insufficient_quota'}}
            mock_response.text = 'Insufficient quota'
            mock_post.return_value = mock_response

            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
                transcriber = WhisperTranscriber()
                result = transcriber.transcribe_audio(temp_path)

                # Should return None but service should remain available
                self.assertIsNone(result)
                self.assertTrue(transcriber.available)

        finally:
            os.unlink(temp_path)

    @patch('models.whisper_transcriber.requests.post')
    def test_transcribe_audio_other_error_status(self, mock_post):
        """Test transcription with other HTTP error status"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(b'dummy audio content')
            temp_path = temp_file.name

        try:
            # Mock 500 error response
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = 'Internal server error'
            mock_post.return_value = mock_response

            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
                transcriber = WhisperTranscriber()
                result = transcriber.transcribe_audio(temp_path)

                # Should return None
                self.assertIsNone(result)

        finally:
            os.unlink(temp_path)

    @patch('models.whisper_transcriber.requests.post')
    def test_transcribe_audio_exception(self, mock_post):
        """Test transcription with general exception"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(b'dummy audio content')
            temp_path = temp_file.name

        try:
            # Mock request exception
            mock_post.side_effect = Exception("Network error")

            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
                transcriber = WhisperTranscriber()
                result = transcriber.transcribe_audio(temp_path)

                # Should return None
                self.assertIsNone(result)

        finally:
            os.unlink(temp_path)

    @patch('models.whisper_transcriber.requests.post')
    def test_transcribe_audio_legacy_method(self, mock_post):
        """Test legacy transcribe_audio method"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(b'dummy audio content')
            temp_path = temp_file.name

        try:
            # Mock successful API response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'text': 'Legacy transcript'}
            mock_post.return_value = mock_response

            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
                transcriber = WhisperTranscriber()
                result = transcriber.transcribe_audio_legacy(temp_path)

                # Should return just the text
                self.assertEqual(result, 'Legacy transcript')

        finally:
            os.unlink(temp_path)

    @patch('models.whisper_transcriber.requests.post')
    def test_transcribe_audio_legacy_method_failure(self, mock_post):
        """Test legacy transcribe_audio method with failure"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            transcriber = WhisperTranscriber()

            # Mock failure
            with patch.object(transcriber, 'transcribe_audio', return_value=None):
                result = transcriber.transcribe_audio_legacy("dummy_path.mp3")
                self.assertIsNone(result)

    def test_get_service_status_available(self):
        """Test get_service_status when service is available"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            transcriber = WhisperTranscriber()
            status = transcriber.get_service_status()

            expected = {
                'available': True,
                'api_key_set': True,
                'service_name': 'whisper'
            }
            self.assertEqual(status, expected)

    def test_get_service_status_not_available(self):
        """Test get_service_status when service is not available"""
        transcriber = WhisperTranscriber()
        status = transcriber.get_service_status()

        expected = {
            'available': False,
            'api_key_set': False,
            'service_name': 'whisper'
        }
        self.assertEqual(status, expected)

    @patch('models.whisper_transcriber.TranscriptionQualityAnalyzer.calculate_text_quality_score')
    @patch('models.whisper_transcriber.requests.post')
    def test_confidence_calculation(self, mock_post, mock_calculate_score):
        """Test that confidence is calculated and boosted for Whisper"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(b'dummy audio content')
            temp_path = temp_file.name

        try:
            # Mock quality score of 0.8, expect final confidence of 0.9 (boosted by 0.1)
            mock_calculate_score.return_value = 0.8

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'text': 'Test transcript'}
            mock_post.return_value = mock_response

            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
                transcriber = WhisperTranscriber()
                result = transcriber.transcribe_audio(temp_path)

                self.assertIsNotNone(result)
                self.assertAlmostEqual(result.confidence, 0.9, places=3)
                mock_calculate_score.assert_called_once_with('Test transcript')

        finally:
            os.unlink(temp_path)

    @patch('models.whisper_transcriber.TranscriptionQualityAnalyzer.calculate_text_quality_score')
    @patch('models.whisper_transcriber.requests.post')
    def test_confidence_calculation_capped(self, mock_post, mock_calculate_score):
        """Test that confidence is capped at 1.0"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(b'dummy audio content')
            temp_path = temp_file.name

        try:
            # Mock quality score of 0.95, expect final confidence of 1.0 (capped)
            mock_calculate_score.return_value = 0.95

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'text': 'Test transcript'}
            mock_post.return_value = mock_response

            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
                transcriber = WhisperTranscriber()
                result = transcriber.transcribe_audio(temp_path)

                self.assertIsNotNone(result)
                self.assertEqual(result.confidence, 1.0)
                mock_calculate_score.assert_called_once_with('Test transcript')

        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()
