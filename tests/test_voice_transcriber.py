import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from src.models.voice_transcriber import VoiceTranscriber


class TestVoiceTranscriber:
    """Test cases for VoiceTranscriber class"""
    
    def setup_method(self):
        """Set up test environment"""
        # Clear environment variables for testing
        self.original_env = {}
        for key in ['WHISPER_API_KEY', 'HUGGINGFACE_TOKEN', 'OPENAI_API_KEY']:
            if key in os.environ:
                self.original_env[key] = os.environ[key]
                del os.environ[key]
    
    def teardown_method(self):
        """Restore environment variables"""
        for key, value in self.original_env.items():
            os.environ[key] = value
    
    def test_init_no_api_keys(self):
        """Test initialization without API keys"""
        transcriber = VoiceTranscriber()
        
        assert transcriber.services_available['whisper_api'] == False
        assert transcriber.services_available['huggingface'] == False
        assert transcriber.services_available['openai_whisper'] == False
    
    def test_init_with_api_keys(self):
        """Test initialization with API keys"""
        os.environ['WHISPER_API_KEY'] = 'test_key'
        os.environ['HUGGINGFACE_TOKEN'] = 'test_token'
        
        transcriber = VoiceTranscriber()
        
        assert transcriber.services_available['whisper_api'] == True
        assert transcriber.services_available['huggingface'] == True
        assert transcriber.services_available['openai_whisper'] == False
    
    @patch('requests.post')
    @patch('requests.get')
    def test_download_voice_file_success(self, mock_get, mock_post):
        """Test successful voice file download"""
        # Mock file info response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'ok': True,
            'result': {'file_path': 'voice/file_123.ogg'}
        }
        
        # Mock file download response
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b'fake_audio_data'
        
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        transcriber = VoiceTranscriber()
        
        result = transcriber._download_voice_file('test_file_id')
        
        assert result == b'fake_audio_data'
        mock_post.assert_called_once()
        mock_get.assert_called_once()
    
    @patch('requests.post')
    def test_download_voice_file_failure(self, mock_post):
        """Test voice file download failure"""
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = 'Bad Request'
        
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        transcriber = VoiceTranscriber()
        
        result = transcriber._download_voice_file('test_file_id')
        
        assert result is None
    
    @patch('requests.post')
    def test_transcribe_with_whisper_api_success(self, mock_post):
        """Test successful transcription with Whisper API"""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'text': 'Hello world'}
        
        os.environ['WHISPER_API_KEY'] = 'test_key'
        transcriber = VoiceTranscriber()
        
        result = transcriber._transcribe_with_whisper_api(b'fake_audio')
        
        assert result == 'Hello world'
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_transcribe_with_whisper_api_failure(self, mock_post):
        """Test transcription failure with Whisper API"""
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = 'Bad Request'
        
        os.environ['WHISPER_API_KEY'] = 'test_key'
        transcriber = VoiceTranscriber()
        
        result = transcriber._transcribe_with_whisper_api(b'fake_audio')
        
        assert result is None
    
    @patch('requests.post')
    def test_transcribe_with_huggingface_success(self, mock_post):
        """Test successful transcription with Hugging Face"""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'text': 'Hello world'}
        
        os.environ['HUGGINGFACE_TOKEN'] = 'test_token'
        transcriber = VoiceTranscriber()
        
        result = transcriber._transcribe_with_huggingface(b'fake_audio')
        
        assert result == 'Hello world'
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_transcribe_with_huggingface_list_response(self, mock_post):
        """Test transcription with Hugging Face list response format"""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = [{'text': 'Hello world'}]
        
        os.environ['HUGGINGFACE_TOKEN'] = 'test_token'
        transcriber = VoiceTranscriber()
        
        result = transcriber._transcribe_with_huggingface(b'fake_audio')
        
        assert result == 'Hello world'
    
    @patch('requests.post')
    @patch('requests.get')
    def test_transcribe_voice_message_success(self, mock_get, mock_post):
        """Test successful voice message transcription"""
        # Mock file download
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'ok': True,
            'result': {'file_path': 'voice/file_123.ogg'}
        }
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b'fake_audio_data'
        
        # Mock transcription service
        with patch.object(VoiceTranscriber, '_transcribe_with_whisper_api') as mock_transcribe:
            mock_transcribe.return_value = 'Hello world'
            
            os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
            os.environ['WHISPER_API_KEY'] = 'test_key'
            transcriber = VoiceTranscriber()
            
            result = transcriber.transcribe_voice_message('test_file_id')
            
            assert result == 'Hello world'
    
    @patch('requests.post')
    @patch('requests.get')
    def test_transcribe_voice_message_fallback(self, mock_get, mock_post):
        """Test voice message transcription with fallback"""
        # Mock file download
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'ok': True,
            'result': {'file_path': 'voice/file_123.ogg'}
        }
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b'fake_audio_data'
        
        # Mock transcription services - first fails, second succeeds
        with patch.object(VoiceTranscriber, '_transcribe_with_whisper_api') as mock_whisper:
            with patch.object(VoiceTranscriber, '_transcribe_with_huggingface') as mock_hf:
                mock_whisper.return_value = None
                mock_hf.return_value = 'Hello world'
                
                os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
                os.environ['WHISPER_API_KEY'] = 'test_key'
                os.environ['HUGGINGFACE_TOKEN'] = 'test_token'
                transcriber = VoiceTranscriber()
                
                result = transcriber.transcribe_voice_message('test_file_id')
                
                assert result == 'Hello world'
                mock_whisper.assert_called_once()
                mock_hf.assert_called_once()
    
    @patch('requests.post')
    @patch('requests.get')
    def test_transcribe_voice_message_all_fail(self, mock_get, mock_post):
        """Test voice message transcription when all services fail"""
        # Mock file download
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            'ok': True,
            'result': {'file_path': 'voice/file_123.ogg'}
        }
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b'fake_audio_data'
        
        # Mock all transcription services to fail
        with patch.object(VoiceTranscriber, '_transcribe_with_whisper_api') as mock_whisper:
            with patch.object(VoiceTranscriber, '_transcribe_with_huggingface') as mock_hf:
                with patch.object(VoiceTranscriber, '_transcribe_with_openai_whisper') as mock_openai:
                    mock_whisper.return_value = None
                    mock_hf.return_value = None
                    mock_openai.return_value = None
                    
                    os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
                    os.environ['WHISPER_API_KEY'] = 'test_key'
                    os.environ['HUGGINGFACE_TOKEN'] = 'test_token'
                    os.environ['OPENAI_API_KEY'] = 'test_key'
                    transcriber = VoiceTranscriber()
                    
                    result = transcriber.transcribe_voice_message('test_file_id')
                    
                    assert result is None
    
    def test_get_service_status(self):
        """Test getting service status"""
        transcriber = VoiceTranscriber()
        status = transcriber.get_service_status()
        
        assert 'services_available' in status
        assert 'rate_limits' in status
        assert 'whisper_api' in status['services_available']
        assert 'huggingface' in status['services_available']
        assert 'openai_whisper' in status['services_available']
    
    def test_respect_rate_limit(self):
        """Test rate limiting functionality"""
        transcriber = VoiceTranscriber()
        
        # First call should not sleep
        with patch('time.sleep') as mock_sleep:
            transcriber._respect_rate_limit('whisper_api')
            # Should not sleep on first call
            assert mock_sleep.call_count == 0
        
        # Second call immediately after should sleep due to rate limiting
        with patch('time.sleep') as mock_sleep:
            transcriber._respect_rate_limit('whisper_api')
            # Should sleep due to rate limiting
            assert mock_sleep.call_count == 1
