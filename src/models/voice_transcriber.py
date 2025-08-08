import os
import logging
import requests
import time
import tempfile
from typing import Optional, Dict, List
from urllib.parse import urlparse
import json

# Import new transcription services
try:
    import assemblyai as aai
    ASSEMBLYAI_AVAILABLE = True
except ImportError:
    ASSEMBLYAI_AVAILABLE = False

try:
    from google.cloud import speech
    from google.api_core.exceptions import GoogleAPICallError, ResourceExhausted
    GOOGLE_SPEECH_AVAILABLE = True
except ImportError:
    GOOGLE_SPEECH_AVAILABLE = False

logger = logging.getLogger(__name__)

class VoiceTranscriber:
    """Voice transcription service with AssemblyAI and Google Speech-to-Text as primary services"""
    
    def __init__(self):
        self.rate_limits = {
            'assemblyai': {'last_request': 0, 'min_interval': 1},  # 1 second between requests
            'google_speech': {'last_request': 0, 'min_interval': 1},  # 1 second between requests
        }
        
        # API keys and endpoints
        self.assemblyai_api_key = os.getenv('ASSEMBLYAI_API_KEY')
        self.google_credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        # Service availability flags
        self.services_available = self._check_service_availability()
        
    def _check_service_availability(self) -> Dict[str, bool]:
        """Check which transcription services are available"""
        services = {
            'assemblyai': bool(self.assemblyai_api_key and ASSEMBLYAI_AVAILABLE),
            'google_speech': bool(self.google_credentials and GOOGLE_SPEECH_AVAILABLE),
        }
        
        # Log service availability for debugging
        logger.info(f"Voice transcription services available: {services}")
        
        return services
    
    def _respect_rate_limit(self, service: str) -> None:
        """Ensure rate limiting is respected for each service"""
        if service in self.rate_limits:
            last_request = self.rate_limits[service]['last_request']
            min_interval = self.rate_limits[service]['min_interval']
            
            time_since_last = time.time() - last_request
            if time_since_last < min_interval:
                sleep_time = min_interval - time_since_last
                logger.info(f"Rate limiting {service}, sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            self.rate_limits[service]['last_request'] = time.time()
    
    def _download_voice_file(self, file_id: str) -> Optional[bytes]:
        """Download voice file from Telegram"""
        try:
            # Get file info from Telegram
            token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not token:
                logger.error("TELEGRAM_BOT_TOKEN not found")
                return None
            
            # Get file info
            file_info_url = f"https://api.telegram.org/bot{token}/getFile"
            file_info_response = requests.post(file_info_url, json={'file_id': file_id}, timeout=10)
            
            if file_info_response.status_code != 200:
                logger.error(f"Failed to get file info: {file_info_response.text}")
                return None
            
            file_info = file_info_response.json()
            if not file_info.get('ok'):
                logger.error(f"File info response not ok: {file_info}")
                return None
            
            # Download the file
            file_url = f"https://api.telegram.org/file/bot{token}/{file_info['result']['file_path']}"
            file_response = requests.get(file_url, timeout=30)
            
            if file_response.status_code != 200:
                logger.error(f"Failed to download file: {file_response.status_code}")
                return None
            
            return file_response.content
            
        except (OSError, ImportError, AttributeError, ValueError, requests.RequestException) as e:
            logger.error(f"Error downloading voice file: {e}")
            return None
    
    def _save_audio_to_temp_file(self, audio_data: bytes) -> Optional[str]:
        """Save audio data to temporary file"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            return temp_file_path
        except (OSError, ImportError, AttributeError, ValueError) as e:
            logger.error(f"Error saving audio to temp file: {e}")
            return None
    
    def _detect_language_assemblyai(self, audio_path: str) -> Optional[str]:
        """Quickly detect spoken language using AssemblyAI"""
        try:
            self._respect_rate_limit('assemblyai')
            
            aai.settings.api_key = self.assemblyai_api_key
            transcriber = aai.Transcriber()
            
            transcript = transcriber.transcribe(
                audio_path,
                config=aai.TranscriptionConfig(language_detection=True)
            )
            
            if transcript.language_code:
                logger.info(f"[INFO] AssemblyAI detected language: {transcript.language_code}")
                return transcript.language_code
            else:
                logger.warning("[WARN] AssemblyAI language detection failed")
                return None
                
        except (OSError, ImportError, AttributeError, ValueError, requests.RequestException) as e:
            logger.error(f"[ERROR] AssemblyAI language detection failed: {e}")
            return None
    
    def _transcribe_with_assemblyai(self, audio_path: str) -> Optional[str]:
        """Full transcription with AssemblyAI (auto language detection)"""
        try:
            self._respect_rate_limit('assemblyai')
            
            aai.settings.api_key = self.assemblyai_api_key
            transcriber = aai.Transcriber()
            
            transcript = transcriber.transcribe(
                audio_path,
                config=aai.TranscriptionConfig(language_detection=True)
            )
            
            if transcript.text:
                logger.info(f"[SUCCESS] AssemblyAI transcription: '{transcript.text[:50]}...'")
                return transcript.text.strip()
            else:
                logger.warning("[WARN] AssemblyAI returned empty transcription")
                return None
                
        except (OSError, ImportError, AttributeError, ValueError, requests.RequestException) as e:
            logger.error(f"[ERROR] AssemblyAI transcription failed: {e}")
            return None
    
    def _transcribe_with_google_speech(self, audio_path: str, language_code: str = None) -> Optional[str]:
        """Full transcription using Google Speech-to-Text"""
        try:
            self._respect_rate_limit('google_speech')
            
            client = speech.SpeechClient()
            
            with open(audio_path, "rb") as f:
                content = f.read()
            
            audio = speech.RecognitionAudio(content=content)
            
            # Use detected language or auto-detect
            config_language = language_code if language_code else "en-US"
            
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                sample_rate_hertz=48000,  # Telegram voice messages are typically 48kHz
                language_code=config_language,
                enable_automatic_punctuation=True
            )
            
            response = client.recognize(config=config, audio=audio)
            
            if response.results:
                transcript = " ".join([result.alternatives[0].transcript for result in response.results])
                logger.info(f"[SUCCESS] Google Speech transcription: '{transcript[:50]}...'")
                return transcript.strip()
            else:
                logger.warning("[WARN] Google Speech returned empty transcription")
                return None
                
        except (GoogleAPICallError, ResourceExhausted) as e:
            logger.error(f"[ERROR] Google Speech API failed: {e}")
            return None
        except (OSError, ImportError, AttributeError, ValueError) as e:
            logger.error(f"[ERROR] Google Speech unexpected error: {e}")
            return None
    
    def transcribe_voice_message(self, file_id: str) -> Optional[str]:
        """Transcribe voice message with intelligent fallback strategy"""
        logger.info(f"Starting voice transcription for file: {file_id}")
        
        # Download the voice file
        audio_data = self._download_voice_file(file_id)
        if not audio_data:
            logger.error("Failed to download voice file")
            return None
        
        logger.info(f"Downloaded voice file, size: {len(audio_data)} bytes")
        
        # Save to temporary file for services that need file paths
        temp_audio_path = self._save_audio_to_temp_file(audio_data)
        if not temp_audio_path:
            logger.error("Failed to save audio to temp file")
            return None
        
        try:
            transcript = None
            
            # Step 1: Try AssemblyAI (primary service)
            if self.services_available.get('assemblyai', False):
                logger.info("[INFO] Trying AssemblyAI transcription...")
                transcript = self._transcribe_with_assemblyai(temp_audio_path)
                if transcript:
                    return transcript
            
            # Step 2: Try Google Speech-to-Text with language detection
            if self.services_available.get('google_speech', False):
                logger.info("[INFO] Trying Google Speech-to-Text...")
                
                # First detect language with AssemblyAI if available
                detected_language = None
                if self.services_available.get('assemblyai', False):
                    detected_language = self._detect_language_assemblyai(temp_audio_path)
                
                try:
                    transcript = self._transcribe_with_google_speech(temp_audio_path, detected_language)
                    if transcript:
                        return transcript
                except (OSError, ImportError, AttributeError, ValueError, requests.RequestException) as e:
                    logger.warning(f"[WARN] Google Speech-to-Text failed: {e}")
            
            logger.error("[FATAL] All transcription services failed")
            return None
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_audio_path)
            except (OSError, ImportError, AttributeError, ValueError) as e:
                logger.warning(f"Failed to clean up temp file: {e}")
    
    def get_service_status(self) -> Dict[str, Dict]:
        """Get status of all transcription services"""
        return {
            'services_available': self.services_available,
            'rate_limits': {
                service: {
                    'last_request': info['last_request'],
                    'min_interval': info['min_interval']
                }
                for service, info in self.rate_limits.items()
            },
            'primary_services': ['assemblyai', 'google_speech']
        }
