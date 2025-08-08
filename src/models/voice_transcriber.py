import os
import logging
import requests
import time
import tempfile
from typing import Optional, Dict, List
from urllib.parse import urlparse
import json

logger = logging.getLogger(__name__)

class VoiceTranscriber:
    """Voice transcription service with multiple free model fallbacks"""
    
    def __init__(self):
        self.rate_limits = {
            'whisper_api': {'last_request': 0, 'min_interval': 1},  # 1 second between requests
            'huggingface': {'last_request': 0, 'min_interval': 2},  # 2 seconds between requests
            'openai_whisper': {'last_request': 0, 'min_interval': 1},  # 1 second between requests
        }
        
        # API keys and endpoints
        self.whisper_api_key = os.getenv('WHISPER_API_KEY')
        self.huggingface_token = os.getenv('HUGGINGFACE_TOKEN')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Service availability flags
        self.services_available = self._check_service_availability()
        
    def _check_service_availability(self) -> Dict[str, bool]:
        """Check which transcription services are available"""
        return {
            'whisper_api': bool(self.whisper_api_key),
            'huggingface': bool(self.huggingface_token),
            'openai_whisper': bool(self.openai_api_key),
        }
    
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
    
    def _download_voice_file(self, file_path: str) -> Optional[bytes]:
        """Download voice file from Telegram"""
        try:
            # Get file info from Telegram
            token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not token:
                logger.error("TELEGRAM_BOT_TOKEN not found")
                return None
            
            # Get file info
            file_info_url = f"https://api.telegram.org/bot{token}/getFile"
            file_info_response = requests.post(file_info_url, json={'file_id': file_path}, timeout=10)
            
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
            
        except Exception as e:
            logger.error(f"Error downloading voice file: {e}")
            return None
    
    def _transcribe_with_whisper_api(self, audio_data: bytes) -> Optional[str]:
        """Transcribe using Whisper API (free tier)"""
        try:
            self._respect_rate_limit('whisper_api')
            
            url = "https://api.openai.com/v1/audio/transcriptions"
            headers = {
                "Authorization": f"Bearer {self.whisper_api_key}"
            }
            
            files = {
                'file': ('audio.ogg', audio_data, 'audio/ogg'),
                'model': (None, 'whisper-1'),
                'language': (None, 'auto')
            }
            
            response = requests.post(url, headers=headers, files=files, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('text', '').strip()
            else:
                logger.warning(f"Whisper API failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error with Whisper API: {e}")
            return None
    
    def _transcribe_with_huggingface(self, audio_data: bytes) -> Optional[str]:
        """Transcribe using Hugging Face free models"""
        try:
            self._respect_rate_limit('huggingface')
            
            # Use a free Whisper model on Hugging Face
            url = "https://api-inference.huggingface.co/models/openai/whisper-base"
            headers = {
                "Authorization": f"Bearer {self.huggingface_token}"
            }
            
            response = requests.post(url, headers=headers, data=audio_data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, dict) and 'text' in result:
                    return result['text'].strip()
                elif isinstance(result, list) and len(result) > 0:
                    return result[0].get('text', '').strip()
            else:
                logger.warning(f"Hugging Face API failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error with Hugging Face API: {e}")
            return None
    
    def _transcribe_with_openai_whisper(self, audio_data: bytes) -> Optional[str]:
        """Transcribe using OpenAI Whisper (alternative endpoint)"""
        try:
            self._respect_rate_limit('openai_whisper')
            
            # Try alternative Whisper endpoint
            url = "https://api.openai.com/v1/audio/transcriptions"
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}"
            }
            
            files = {
                'file': ('audio.ogg', audio_data, 'audio/ogg'),
                'model': (None, 'whisper-1'),
                'response_format': (None, 'text')
            }
            
            response = requests.post(url, headers=headers, files=files, timeout=30)
            
            if response.status_code == 200:
                return response.text.strip()
            else:
                logger.warning(f"OpenAI Whisper failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error with OpenAI Whisper: {e}")
            return None
    
    def transcribe_voice_message(self, file_path: str) -> Optional[str]:
        """Transcribe voice message with fallback to multiple services"""
        logger.info(f"Starting voice transcription for file: {file_path}")
        
        # Download the voice file
        audio_data = self._download_voice_file(file_path)
        if not audio_data:
            logger.error("Failed to download voice file")
            return None
        
        logger.info(f"Downloaded voice file, size: {len(audio_data)} bytes")
        
        # Try each transcription service in order
        transcription_services = [
            ('whisper_api', self._transcribe_with_whisper_api),
            ('huggingface', self._transcribe_with_huggingface),
            ('openai_whisper', self._transcribe_with_openai_whisper),
        ]
        
        for service_name, service_func in transcription_services:
            if not self.services_available.get(service_name, False):
                logger.info(f"Service {service_name} not available, skipping")
                continue
            
            logger.info(f"Trying transcription with {service_name}")
            try:
                transcription = service_func(audio_data)
                if transcription:
                    logger.info(f"Successfully transcribed with {service_name}: '{transcription[:50]}...'")
                    return transcription
                else:
                    logger.warning(f"Service {service_name} returned empty transcription")
            except Exception as e:
                logger.error(f"Error with {service_name}: {e}")
                continue
        
        logger.error("All transcription services failed")
        return None
    
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
            }
        }
