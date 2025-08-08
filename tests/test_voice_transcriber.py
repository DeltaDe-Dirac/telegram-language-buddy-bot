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
        for key in ['ASSEMBLYAI_API_KEY', 'GOOGLE_APPLICATION_CREDENTIALS', 'TELEGRAM_BOT_TOKEN']:
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
        
        assert transcriber.services_available['assemblyai'] == False
        assert transcriber.services_available['google_speech'] == False
    
    def test_init_with_api_keys(self):
        """Test initialization with API keys"""
        os.environ['ASSEMBLYAI_API_KEY'] = 'test_key'
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'test_credentials.json'
        
        transcriber = VoiceTranscriber()
        
        assert transcriber.services_available['assemblyai'] == True
        assert transcriber.services_available['google_speech'] == True
    
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
        
        # Set required environment variable
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
        
        transcriber = VoiceTranscriber()
        result = transcriber._download_voice_file('test_file_id')
        
        assert result == b'fake_audio_data'
    
    @patch('requests.post')
    def test_download_voice_file_failure(self, mock_post):
        """Test voice file download failure"""
        mock_post.return_value.status_code = 404
        mock_post.return_value.text = 'File not found'
        
        transcriber = VoiceTranscriber()
        result = transcriber._download_voice_file('test_file_id')
        
        assert result is None
    
    @patch('src.models.voice_transcriber.ASSEMBLYAI_AVAILABLE', True)
    @patch('src.models.voice_transcriber.aai')
    def test_transcribe_with_assemblyai_success(self, mock_aai):
        """Test successful AssemblyAI transcription"""
        # Mock AssemblyAI response
        mock_transcript = Mock()
        mock_transcript.text = "Hello world"
        mock_aai.Transcriber.return_value.transcribe.return_value = mock_transcript
        
        os.environ['ASSEMBLYAI_API_KEY'] = 'test_key'
        transcriber = VoiceTranscriber()
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = '/tmp/test.ogg'
            result = transcriber._transcribe_with_assemblyai('/tmp/test.ogg')
        
        assert result == "Hello world"
    
    @patch('src.models.voice_transcriber.ASSEMBLYAI_AVAILABLE', True)
    @patch('src.models.voice_transcriber.aai')
    def test_transcribe_with_assemblyai_failure(self, mock_aai):
        """Test AssemblyAI transcription failure"""
        mock_aai.Transcriber.return_value.transcribe.side_effect = Exception("API Error")
        
        os.environ['ASSEMBLYAI_API_KEY'] = 'test_key'
        transcriber = VoiceTranscriber()
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = '/tmp/test.ogg'
            result = transcriber._transcribe_with_assemblyai('/tmp/test.ogg')
        
        assert result is None
    
    @patch('src.models.voice_transcriber.GOOGLE_SPEECH_AVAILABLE', True)
    @patch('src.models.voice_transcriber.speech')
    def test_transcribe_with_google_speech_success(self, mock_speech):
        """Test successful Google Speech-to-Text transcription"""
        # Mock Google Speech response
        mock_result = Mock()
        mock_result.alternatives = [Mock(transcript="Hello world")]
        mock_response = Mock()
        mock_response.results = [mock_result]
        mock_speech.SpeechClient.return_value.recognize.return_value = mock_response
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'test_credentials.json'
        transcriber = VoiceTranscriber()
        
        with patch('builtins.open', mock_open(read_data=b'fake_audio')):
            result = transcriber._transcribe_with_google_speech('/tmp/test.ogg')
        
        assert result == "Hello world"
    
    @patch('src.models.voice_transcriber.GOOGLE_SPEECH_AVAILABLE', True)
    @patch('src.models.voice_transcriber.speech')
    def test_transcribe_with_google_speech_failure(self, mock_speech):
        """Test Google Speech-to-Text transcription failure"""
        mock_speech.SpeechClient.return_value.recognize.side_effect = Exception("API Error")
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'test_credentials.json'
        transcriber = VoiceTranscriber()
        
        with patch('builtins.open', mock_open(read_data=b'fake_audio')):
            result = transcriber._transcribe_with_google_speech('/tmp/test.ogg')
        
        assert result is None
    
    @patch('src.models.voice_transcriber.VoiceTranscriber._download_voice_file')
    @patch('src.models.voice_transcriber.VoiceTranscriber._transcribe_with_assemblyai')
    def test_transcribe_voice_message_success(self, mock_transcribe, mock_download):
        """Test successful voice message transcription"""
        mock_download.return_value = b'fake_audio_data'
        mock_transcribe.return_value = "Hello world"
        
        os.environ['ASSEMBLYAI_API_KEY'] = 'test_key'
        transcriber = VoiceTranscriber()
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = '/tmp/test.ogg'
            result = transcriber.transcribe_voice_message('test_file_id')
        
        assert result == "Hello world"
    
    @patch('src.models.voice_transcriber.VoiceTranscriber._download_voice_file')
    def test_transcribe_voice_message_all_fail(self, mock_download):
        """Test voice message transcription when all services fail"""
        mock_download.return_value = b'fake_audio_data'
        
        transcriber = VoiceTranscriber()
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = '/tmp/test.ogg'
            result = transcriber.transcribe_voice_message('test_file_id')
        
        assert result is None
    
    def test_get_service_status(self):
        """Test service status retrieval"""
        transcriber = VoiceTranscriber()
        status = transcriber.get_service_status()
        
        assert 'services_available' in status
        assert 'rate_limits' in status
        assert 'primary_services' in status
        assert 'assemblyai' in status['services_available']
        assert 'google_speech' in status['services_available']
    
    @patch('time.sleep')
    @patch('time.time')
    def test_respect_rate_limit(self, mock_time, mock_sleep):
        """Test rate limiting functionality"""
        # Set up time to return 0 for first call, then 0.5 for second call
        mock_time.side_effect = [0, 0.5]
        
        transcriber = VoiceTranscriber()
        
        # First call should sleep because time difference is 0 < min_interval (1)
        transcriber._respect_rate_limit('assemblyai')
        mock_sleep.assert_called_once_with(1.0)  # Should sleep for full interval
        
        # Reset mock for second test
        mock_sleep.reset_mock()
        mock_time.side_effect = [1.5, 2.0]  # More than 1 second apart
        
        # Second call should not sleep because time difference > min_interval
        transcriber._respect_rate_limit('assemblyai')
        mock_sleep.assert_not_called()


def mock_open(read_data):
    """Helper function to mock file open"""
    mock_file = Mock()
    mock_file.read.return_value = read_data
    mock_file.__enter__ = Mock(return_value=mock_file)
    mock_file.__exit__ = Mock(return_value=None)
    return Mock(return_value=mock_file)
