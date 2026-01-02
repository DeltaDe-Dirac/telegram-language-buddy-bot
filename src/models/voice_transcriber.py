import os
import logging
import requests
import time
import tempfile
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse
import json
from .transcription_result import TranscriptionResult, TranscriptionQualityAnalyzer

# Import new transcription services
try:
    import assemblyai as aai
    ASSEMBLYAI_AVAILABLE = True
except ImportError:
    ASSEMBLYAI_AVAILABLE = False

try:
    from google.cloud import speech
    from google.api_core.exceptions import GoogleAPICallError
    GOOGLE_SPEECH_AVAILABLE = True
except ImportError:
    GOOGLE_SPEECH_AVAILABLE = False

try:
    from .whisper_transcriber import WhisperTranscriber
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

logger = logging.getLogger(__name__)


def _mask_key(key: Optional[str]) -> str:
    if not key:
        return '<unset>'
    try:
        return key[:6] + '...' + key[-4:]
    except Exception:
        return '<masked>'

class VoiceTranscriber:
    """Voice transcription service with AssemblyAI and Google Speech-to-Text as primary services"""
    
    def __init__(self):
        self.rate_limits = {
            'assemblyai': {'last_request': 0, 'min_interval': 1},  # 1 second between requests
            'google_speech': {'last_request': 0, 'min_interval': 1},  # 1 second between requests
            'whisper': {'last_request': 0, 'min_interval': 1},  # 1 second between requests
        }
        
        # API keys and endpoints
        self.assemblyai_api_key = os.getenv('ASSEMBLYAI_API_KEY')
        
        # Handle Google credentials - JSON string only
        self.google_credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        
        # Initialize Whisper transcriber
        if WHISPER_AVAILABLE:
            self.whisper_transcriber = WhisperTranscriber()
        else:
            self.whisper_transcriber = None
        
        # Set up Google credentials if JSON is provided
        if self.google_credentials_json:
            self._setup_google_credentials_from_json()
        else:
            logger.warning("No Google credentials found (GOOGLE_APPLICATION_CREDENTIALS_JSON not set)")
        
        # Service availability flags
        self.services_available = self._check_service_availability()
    
    def _setup_google_credentials_from_json(self) -> None:
        """Set up Google credentials from JSON string"""
        try:
            import json
            from google.oauth2 import service_account
            
            # Parse the JSON credentials to validate they're correct
            credentials_info = json.loads(self.google_credentials_json)

            # Validate credentials by creating them (we don't need to keep the object)
            service_account.Credentials.from_service_account_info(credentials_info)

            logger.info("Successfully validated Google credentials from JSON")
            
        except Exception as e:
            logger.error(f"Failed to set up Google credentials from JSON: {e}")
    
    def _check_service_availability(self) -> Dict[str, bool]:
        """Check which transcription services are available"""
        # Check if Google credentials are available (JSON only)
        google_creds_available = bool(self.google_credentials_json)
        
        services = {
            'assemblyai': bool(self.assemblyai_api_key and ASSEMBLYAI_AVAILABLE),
            'google_speech': bool(google_creds_available and GOOGLE_SPEECH_AVAILABLE),
            'whisper': bool(self.whisper_transcriber and self.whisper_transcriber.available),
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
            token = os.getenv('TELEGRAM_BOT_TOKEN')  # Get file info from Telegram
            if not token: logger.error("TELEGRAM_BOT_TOKEN not found"); return None
            
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
            
        except requests.RequestException as e:
            logger.error(f"Error downloading voice file (network): {e}")
            return None
        except Exception as e:
            logger.error(f"Error downloading voice file: {e}")
            return None
    
    def _save_audio_to_temp_file(self, audio_data: bytes) -> Optional[str]:
        """Save audio data to temporary file"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file: temp_file.write(audio_data); return temp_file.name
        except requests.RequestException as e:
            logger.error(f"Error saving audio to temp file (network): {e}")
            return None
        except Exception as e:
            logger.error(f"Error saving audio to temp file: {e}")
            return None
    
    def _detect_language_assemblyai(self, audio_path: str) -> Optional[str]:
        """Quickly detect spoken language using AssemblyAI"""
        try:
            self._respect_rate_limit('assemblyai'); aai.settings.api_key = self.assemblyai_api_key; transcriber = aai.Transcriber()
            
            # Call the transcriber to warm up / check availability; we don't need the result here
            transcriber.transcribe(
                audio_path,
                config=aai.TranscriptionConfig(language_detection=True)
            )
            
            # AssemblyAI doesn't provide language_code in the current API
            # We'll rely on the language detection in the translator instead
            logger.info("[INFO] AssemblyAI transcription completed, language detection will be done by translator")
            return None
                
        except requests.RequestException as e:
            logger.error(f"[ERROR] AssemblyAI language detection network error: {e}")
            return None
        except Exception as e:
            logger.error(f"[ERROR] AssemblyAI language detection failed: {e}")
            return None
    
    def _transcribe_with_assemblyai(self, audio_path: str) -> Optional[TranscriptionResult]:
        """Full transcription with AssemblyAI (auto language detection) with confidence scoring"""
        try:
            self._respect_rate_limit('assemblyai')
            
            aai.settings.api_key = self.assemblyai_api_key
            transcriber = aai.Transcriber()

            # Log request metadata (mask API key)
            try:
                masked = _mask_key(self.assemblyai_api_key)
                logger.info(f"[INFO] AssemblyAI transcription request: audio_path={audio_path} masked_api_key={masked}")
                logger.debug("[REQUEST_DATA] AssemblyAI config: language_detection=True")
            except Exception:
                logger.debug("[DEBUG] Failed to log AssemblyAI request metadata")

            transcript = transcriber.transcribe(
                audio_path,
                config=aai.TranscriptionConfig(language_detection=True)
            )

            # Log raw transcript object for debugging (repr to avoid SDK serialization issues)
            try:
                logger.debug(f"[RAW_RESPONSE] AssemblyAI transcript repr: {repr(transcript)[:2000]}")
            except Exception:
                pass
            
            if transcript.text:
                # AssemblyAI provides confidence scores for each word
                # Calculate average confidence across all words
                confidence = 0.8  # Default confidence
                
                if hasattr(transcript, 'words') and transcript.words:
                    total_confidence = sum(word.confidence for word in transcript.words if hasattr(word, 'confidence'))
                    confidence = total_confidence / len(transcript.words)
                else:
                    # Fallback to text quality analysis
                    confidence = TranscriptionQualityAnalyzer.calculate_text_quality_score(transcript.text)
                
                logger.info(f"[SUCCESS] AssemblyAI transcription: '{transcript.text[:50]}...' (confidence: {confidence:.3f})")
                
                return TranscriptionResult(
                    text=transcript.text.strip(),
                    service='assemblyai',
                    confidence=confidence,
                    raw_response={'text': transcript.text, 'words': transcript.words if hasattr(transcript, 'words') else None}
                )
            else:
                logger.warning("[WARN] AssemblyAI returned empty transcription")
                return None
                
        except requests.RequestException as e:
            logger.error(f"[ERROR] AssemblyAI transcription failed: {e}")
            return None
        except Exception as e:
            logger.error(f"[ERROR] AssemblyAI transcription failed: {e}")
            return None
    
    def _transcribe_with_assemblyai_legacy(self, audio_path: str) -> Optional[str]:
        """Legacy method for backward compatibility - returns just the text"""
        result = self._transcribe_with_assemblyai(audio_path)
        return result.text if result else None
    
    def _transcribe_with_google_speech(self, audio_path: str) -> Optional[TranscriptionResult]:
        """Full transcription using Google Speech-to-Text with confidence scoring"""
        try:
            self._respect_rate_limit('google_speech')
            
            # Create credentials from JSON if available
            credentials = None
            if self.google_credentials_json:
                import json
                from google.oauth2 import service_account
                credentials_info = json.loads(self.google_credentials_json)
                credentials = service_account.Credentials.from_service_account_info(credentials_info)
            
            # Create client with credentials
            if credentials:
                client = speech.SpeechClient(credentials=credentials)
            else:
                client = speech.SpeechClient()
            
            with open(audio_path, "rb") as f:
                content = f.read()

            logger.info(f"[INFO] Google Speech request: audio_path={audio_path} content_bytes={len(content)}")
            logger.debug("[REQUEST_DATA] Google config: encoding=OGG_OPUS, sample_rate_hertz=48000, enable_automatic_punctuation=True")

            audio = speech.RecognitionAudio(content=content)

            # Use auto language detection
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                sample_rate_hertz=48000,  # Telegram voice messages are typically 48kHz
                language_code="en-US",  # Default, will auto-detect
                enable_automatic_punctuation=True
            )

            response = client.recognize(config=config, audio=audio)

            # Log raw response for debugging
            try:
                logger.debug(f"[RAW_RESPONSE] Google Speech: {response}")
            except Exception:
                logger.debug("[DEBUG] Could not stringify Google Speech response")

            if response.results:
                # Google provides confidence scores for each result
                total_confidence = 0
                total_results = 0
                transcript_parts = []
                
                for result in response.results:
                    if result.alternatives:
                        alternative = result.alternatives[0]
                        transcript_parts.append(alternative.transcript)
                        total_confidence += alternative.confidence
                        total_results += 1
                
                transcript = " ".join(transcript_parts)
                confidence = total_confidence / total_results if total_results > 0 else 0.8

                logger.info(f"[SUCCESS] Google Speech transcription: '{transcript[:50]}...' (confidence: {confidence:.3f})")

                raw_resp = {'results': [{'transcript': r.alternatives[0].transcript, 'confidence': r.alternatives[0].confidence} for r in response.results if r.alternatives]}
                logger.debug(f"[RAW_RESPONSE_SUMMARY] Google Speech: {raw_resp}")

                return TranscriptionResult(
                    text=transcript.strip(),
                    service='google_speech',
                    confidence=confidence,
                    raw_response=raw_resp
                )
            else:
                logger.warning("[WARN] Google Speech returned empty transcription")
                return None
                
        except GoogleAPICallError as e:
            logger.error(f"[ERROR] Google Speech API failed: {e}")
            return None
        except (OSError, ImportError, AttributeError, ValueError) as e:
            logger.error(f"[ERROR] Google Speech unexpected error: {e}")
            return None
    
    def _transcribe_with_google_speech_legacy(self, audio_path: str) -> Optional[str]:
        """Legacy method for backward compatibility - returns just the text"""
        result = self._transcribe_with_google_speech(audio_path)
        return result.text if result else None
    
    def transcribe_voice_message(self, file_id: str) -> Optional[str]:
        """Transcribe voice message with intelligent fallback strategy (legacy method)"""
        result = self.transcribe_voice_message_with_confidence(file_id)
        return result.text if result else None
    
    def _try_transcription_service(self, service_name: str, temp_audio_path: str, 
                                  confidence_threshold: float, all_results: list) -> Optional[TranscriptionResult]:
        """Try a transcription service and add result if successful"""
        if not self.services_available.get(service_name, False):
            logger.info(f"[SKIP] {service_name} not available")
            return None
        
        logger.info(f"[TRY] {service_name} transcription on {temp_audio_path} (threshold={confidence_threshold})")
        try:
            if service_name == 'whisper':
                result = self.whisper_transcriber.transcribe_audio(temp_audio_path)
            elif service_name == 'assemblyai':
                result = self._transcribe_with_assemblyai(temp_audio_path)
            elif service_name == 'google_speech':
                result = self._transcribe_with_google_speech(temp_audio_path)
            else:
                return None
            
            if result:
                all_results.append(result)
                logger.info(f"[SUCCESS] {service_name} confidence: {result.confidence:.3f}")
                # Log a short preview of the transcription and raw response for debugging
                try:
                    raw = getattr(result, 'raw_response', None)
                    logger.debug(f"[RAW_RESPONSE] {service_name}: {raw}")
                except Exception:
                    pass
                logger.debug(f"[TRANSCRIPT_PREVIEW] {service_name}: {result.text[:200]!r}")
                
                # If service has high confidence, we can stop here
                if result.is_high_confidence(confidence_threshold):
                    logger.info(f"[HIT] {service_name} reached high confidence ({result.confidence:.3f}), using result")
                    return result
        except Exception as e:
            logger.exception(f"[WARN] {service_name} failed with exception")
        
        return None
    
    def transcribe_voice_message_with_confidence(self, file_id: str, confidence_threshold: float = 0.7) -> Optional[TranscriptionResult]:
        """Transcribe voice message with confidence-based fallback strategy"""
        logger.info(f"Starting confidence-based voice transcription for file: {file_id}")
        
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
            all_results = []
            
            # Try services in order: Whisper, AssemblyAI, Google Speech
            for service_name in ['whisper', 'assemblyai', 'google_speech']:
                result = self._try_transcription_service(service_name, temp_audio_path, confidence_threshold, all_results)
                if result:
                    return result
            
            # Compare all results and choose the best one
            if all_results:
                logger.info(f"[INFO] Comparing {len(all_results)} transcription results...")
                best_result = TranscriptionQualityAnalyzer.compare_transcriptions(all_results)
                logger.info(f"[INFO] Selected {best_result.service} with confidence {best_result.confidence:.3f}")
                return best_result
            
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
            'primary_services': ['whisper', 'assemblyai', 'google_speech']
        }
