import os
import logging
import requests
import tempfile
from typing import Optional, Tuple
import json
from .transcription_result import TranscriptionResult, TranscriptionQualityAnalyzer

logger = logging.getLogger(__name__)


def _mask_key(key: Optional[str]) -> str:
    if not key:
        return '<unset>'
    try:
        return key[:6] + '...' + key[-4:]
    except Exception:
        return '<masked>'

class WhisperTranscriber:
    """Whisper API transcription service"""
    
    def __init__(self):
        # Sanitize OPENAI_API_KEY from environment (strip whitespace and surrounding quotes)
        raw_key = os.getenv('OPENAI_API_KEY') or ''
        sanitized = raw_key.strip().strip('"').strip("'")
        self.api_key = sanitized
        self.base_url = "https://api.openai.com/v1/audio/transcriptions"
        self.available = bool(self.api_key)

        if not self.available:
            logger.warning("Whisper API not available - OPENAI_API_KEY not set or empty after sanitization")
        else:
            # Log masked key presence for debugging (do not log full key)
            try:
                masked = _mask_key(self.api_key)
            except Exception:
                masked = 'set'
            logger.info(f"Whisper API key loaded (masked)={masked}")
    
    def transcribe_audio(self, audio_path: str) -> Optional[TranscriptionResult]:
        """Transcribe audio using Whisper API with confidence scoring"""
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
                # Log request metadata (mask sensitive fields)
                try:
                    file_size = None
                    try:
                        file_size = audio_file.seek(0, 2) or audio_file.tell()
                        audio_file.seek(0)
                    except Exception:
                        file_size = None

                    masked_auth = _mask_key(self.api_key)
                    logger.info(f"[INFO] Sending audio to Whisper API (size={file_size}) masked_auth={masked_auth}")
                    logger.debug(f"[REQUEST_DATA] Whisper data keys: {list(data.keys())}")
                except Exception:
                    logger.debug("[DEBUG] Failed to log Whisper request metadata")

                logger.info("[INFO] Sending audio to Whisper API...")
                response = requests.post(
                    self.base_url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=30
                )
                
                logger.debug(f"[RESPONSE] Whisper status={response.status_code} headers={dict(response.headers)}")

                if response.status_code == 200:
                    result = response.json()
                    logger.debug(f"[RESPONSE_BODY] Whisper: {result}")
                    transcript = result.get('text', '').strip()
                    
                    if transcript:
                        # Calculate confidence based on text quality
                        confidence = TranscriptionQualityAnalyzer.calculate_text_quality_score(transcript)
                        
                        # Whisper doesn't provide confidence scores, so we use text quality analysis
                        # For Whisper, we give a base confidence boost since it's generally very accurate
                        confidence = min(1.0, confidence + 0.1)
                        
                        logger.info(f"[SUCCESS] Whisper transcription: '{transcript[:50]}...' (confidence: {confidence:.3f})")
                        
                        return TranscriptionResult(
                            text=transcript,
                            service='whisper',
                            confidence=confidence,
                            raw_response=result
                        )
                    else:
                        logger.warning("[WARN] Whisper returned empty transcription")
                        return None
                elif response.status_code == 403:
                    # Handle model access issues
                    error_data = response.json()
                    if error_data.get('error', {}).get('code') == 'model_not_found':
                        logger.error("[ERROR] Whisper model not accessible - disabling Whisper service")
                        self.available = False
                        logger.warning("[WARN] Whisper service disabled due to model access issues")
                    else:
                        logger.error(f"[ERROR] Whisper API access denied: {response.status_code} - {response.text}")
                    return None
                else:
                    logger.error(f"[ERROR] Whisper API failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"[ERROR] Whisper transcription failed: {e}")
            return None
    
    def transcribe_audio_legacy(self, audio_path: str) -> Optional[str]:
        """Legacy method for backward compatibility - returns just the text"""
        result = self.transcribe_audio(audio_path)
        return result.text if result else None
    
    def get_service_status(self) -> dict:
        """Get Whisper service status"""
        return {
            'available': self.available,
            'api_key_set': bool(self.api_key),
            'service_name': 'whisper'
        }
