import os
import logging
import requests
import tempfile
from typing import Optional
import json

logger = logging.getLogger(__name__)

class WhisperTranscriber:
    """Whisper API transcription service"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.base_url = "https://api.openai.com/v1/audio/transcriptions"
        self.available = bool(self.api_key)
        
        if not self.available:
            logger.warning("Whisper API not available - OPENAI_API_KEY not set")
    
    def transcribe_audio(self, audio_path: str) -> Optional[str]:
        """Transcribe audio using Whisper API"""
        if not self.available:
            logger.warning("Whisper API not available")
            return None
        
        try:
            with open(audio_path, 'rb') as audio_file:
                files = {'file': audio_file}
                data = {
                    'model': 'whisper-1',
                    'language': None,  # Auto-detect
                    'response_format': 'json'
                }
                headers = {
                    'Authorization': f'Bearer {self.api_key}'
                }
                
                logger.info("[INFO] Sending audio to Whisper API...")
                response = requests.post(
                    self.base_url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    transcript = result.get('text', '').strip()
                    
                    if transcript:
                        logger.info(f"[SUCCESS] Whisper transcription: '{transcript[:50]}...'")
                        return transcript
                    else:
                        logger.warning("[WARN] Whisper returned empty transcription")
                        return None
                else:
                    logger.error(f"[ERROR] Whisper API failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"[ERROR] Whisper transcription failed: {e}")
            return None
    
    def get_service_status(self) -> dict:
        """Get Whisper service status"""
        return {
            'available': self.available,
            'api_key_set': bool(self.api_key),
            'service_name': 'whisper'
        }
