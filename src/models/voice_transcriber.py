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
            
            # AssemblyAI doesn't provide language_code in the current API
            # We'll rely on the language detection in the translator instead
            logger.info(f"[INFO] AssemblyAI transcription completed, language detection will be done by translator")
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
            
            # Enhanced configuration for better language detection
            config = aai.TranscriptionConfig(
                language_detection=True,
                # Add language hints for better accuracy
                language_code="he",  # Try Hebrew first
                # Additional parameters for better transcription
                punctuate=True,
                format_text=True,
                # Enable diarization for better speaker separation
                speaker_labels=True,
                # Improve accuracy for short audio
                boost_param="high"
            )
            
            transcript = transcriber.transcribe(audio_path, config=config)
            
            if transcript.text:
                logger.info(f"[SUCCESS] AssemblyAI transcription: '{transcript.text[:50]}...'")
                return transcript.text.strip()
            else:
                logger.warning("[WARN] AssemblyAI returned empty transcription")
                return None
                
        except (OSError, ImportError, AttributeError, ValueError, requests.RequestException) as e:
            logger.error(f"[ERROR] AssemblyAI transcription failed: {e}")
            return None
    
    def _transcribe_with_google_speech(self, audio_path: str) -> Optional[str]:
        """Full transcription using Google Speech-to-Text"""
        try:
            self._respect_rate_limit('google_speech')
            
            client = speech.SpeechClient()
            
            with open(audio_path, "rb") as f:
                content = f.read()
            
            audio = speech.RecognitionAudio(content=content)
            
            # Enhanced configuration for better language detection
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                sample_rate_hertz=48000,  # Telegram voice messages are typically 48kHz
                # Try Hebrew first, then auto-detect
                language_code="he-IL",  # Hebrew (Israel)
                alternative_language_codes=["en-US", "ru-RU", "ar-IL"],  # Fallback languages
                enable_automatic_punctuation=True,
                enable_word_time_offsets=True,
                enable_word_confidence=True,
                # Use enhanced models for better accuracy
                use_enhanced=True
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
    
    def transcribe_voice_message(self, file_id: str, language_hint: Optional[str] = None) -> Optional[str]:
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
            
            # Step 1: Try AssemblyAI with language hint (primary service)
            if self.services_available.get('assemblyai', False):
                logger.info("[INFO] Trying AssemblyAI transcription...")
                transcript = self._transcribe_with_assemblyai_hinted(temp_audio_path, language_hint)
                if transcript:
                    return transcript
            
            # Step 2: Try Google Speech-to-Text with language hint
            if self.services_available.get('google_speech', False):
                logger.info("[INFO] Trying Google Speech-to-Text...")
                
                try:
                    transcript = self._transcribe_with_google_speech_hinted(temp_audio_path, language_hint)
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
    
    def _transcribe_with_assemblyai_hinted(self, audio_path: str, language_hint: Optional[str] = None) -> Optional[str]:
        """Transcribe with AssemblyAI using language hints"""
        try:
            self._respect_rate_limit('assemblyai')
            
            aai.settings.api_key = self.assemblyai_api_key
            transcriber = aai.Transcriber()
            
            # Map language hints to AssemblyAI language codes (only supported languages)
            # AssemblyAI supports: 'de', 'en', 'en_au', 'en_uk', 'en_us', 'es', 'fi', 'fr', 'hi', 'it', 'ja', 'ko', 'nl', 'pl', 'pt', 'ru', 'tr', 'uk', 'vi', 'zh'
            language_mapping = {
                'ru': 'ru',
                'en': 'en',
                'fr': 'fr',
                'es': 'es',
                'de': 'de',
                'it': 'it',
                'pt': 'pt',
                'ja': 'ja',
                'ko': 'ko',
                'zh': 'zh',
                'hi': 'hi',
                'uk': 'uk',
                'vi': 'vi',
                'pl': 'pl',
                'nl': 'nl',
                'fi': 'fi',
                'tr': 'tr'
            }
            
            # Use language hint if available and supported, otherwise don't specify language
            lang_code = language_mapping.get(language_hint) if language_hint else None
            
            # Enhanced configuration for better language detection
            config_params = {
                'language_detection': True,
                'punctuate': True,
                'format_text': True,
                'speaker_labels': True,
                'boost_param': "high"
            }
            
            # Only add language_code if we have a supported language
            if lang_code:
                config_params['language_code'] = lang_code
                logger.info(f"[INFO] Using AssemblyAI with language hint: {lang_code}")
            else:
                logger.info(f"[INFO] Using AssemblyAI without language hint (unsupported language: {language_hint})")
            
            config = aai.TranscriptionConfig(**config_params)
            
            transcript = transcriber.transcribe(audio_path, config=config)
            
            if transcript.text:
                lang_info = f"({lang_code})" if lang_code else "(auto-detected)"
                logger.info(f"[SUCCESS] AssemblyAI transcription {lang_info}: '{transcript.text[:50]}...'")
                return transcript.text.strip()
            else:
                logger.warning("[WARN] AssemblyAI returned empty transcription")
                return None
                
        except (OSError, ImportError, AttributeError, ValueError, requests.RequestException) as e:
            logger.error(f"[ERROR] AssemblyAI transcription failed: {e}")
            return None
    
    def _transcribe_with_google_speech_hinted(self, audio_path: str, language_hint: Optional[str] = None) -> Optional[str]:
        """Transcribe with Google Speech using language hints"""
        try:
            self._respect_rate_limit('google_speech')
            
            client = speech.SpeechClient()
            
            with open(audio_path, "rb") as f:
                content = f.read()
            
            audio = speech.RecognitionAudio(content=content)
            
            # Map language hints to Google Speech language codes
            language_mapping = {
                'he': 'he-IL',
                'ru': 'ru-RU',
                'en': 'en-US',
                'ar': 'ar-IL',
                'fr': 'fr-FR',
                'es': 'es-ES',
                'de': 'de-DE',
                'it': 'it-IT',
                'pt': 'pt-PT',
                'ja': 'ja-JP',
                'ko': 'ko-KR',
                'zh': 'zh-CN',
                'th': 'th-TH',
                'hi': 'hi-IN',
                'bn': 'bn-IN',
                'ta': 'ta-IN',
                'te': 'te-IN',
                'kn': 'kn-IN',
                'ml': 'ml-IN',
                'gu': 'gu-IN',
                'pa': 'pa-IN',
                'or': 'or-IN',
                'si': 'si-LK',
                'my': 'my-MM',
                'ka': 'ka-GE',
                'am': 'am-ET',
                'uk': 'uk-UA',
                'bg': 'bg-BG',
                'sr': 'sr-RS',
                'el': 'el-GR',
                'fa': 'fa-IR',
                'ur': 'ur-PK',
                'vi': 'vi-VN',
                'id': 'id-ID',
                'ms': 'ms-MY',
                'tl': 'tl-PH',
                'cs': 'cs-CZ',
                'sk': 'sk-SK',
                'hu': 'hu-HU',
                'ro': 'ro-RO',
                'hr': 'hr-HR',
                'sl': 'sl-SI',
                'et': 'et-EE',
                'lv': 'lv-LV',
                'lt': 'lt-LT',
                'pl': 'pl-PL',
                'nl': 'nl-NL',
                'sv': 'sv-SE',
                'da': 'da-DK',
                'no': 'no-NO',
                'fi': 'fi-FI',
                'tr': 'tr-TR'
            }
            
            # Use language hint if available, otherwise default to Hebrew
            primary_lang = language_mapping.get(language_hint, 'he-IL') if language_hint else 'he-IL'
            
            # Enhanced configuration for better language detection
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                sample_rate_hertz=48000,  # Telegram voice messages are typically 48kHz
                # Try primary language first, then auto-detect
                language_code=primary_lang,
                alternative_language_codes=["en-US", "ru-RU", "ar-IL"],  # Fallback languages
                enable_automatic_punctuation=True,
                enable_word_time_offsets=True,
                enable_word_confidence=True,
                # Use enhanced models for better accuracy
                use_enhanced=True
            )
            
            response = client.recognize(config=config, audio=audio)
            
            if response.results:
                transcript = " ".join([result.alternatives[0].transcript for result in response.results])
                logger.info(f"[SUCCESS] Google Speech transcription ({primary_lang}): '{transcript[:50]}...'")
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
