import os
import logging
import requests
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Import transcription services
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

from .language_detector import LanguageDetector
from .free_translator import FreeTranslator
from .database import DatabaseManager
from .voice_transcriber import VoiceTranscriber

logger = logging.getLogger(__name__)

# Constants
REQUEST_TIMEOUT = 10

class TelegramBot:
    """Telegram Bot API integration"""
    
    # Common error messages to avoid duplication
    ERROR_USE_SETPAIR = "❌ An error occurred. Please use /setpair to start over."
    ERROR_INVALID_SELECTION = "❌ Invalid language selection. Please try again."
    ERROR_INVALID_STATE = "❌ Invalid selection state. Please use /setpair to start over."
    ERROR_FAILED_SET_PAIR = "❌ Failed to set language pair. Please try again."
    ERROR_INVALID_CALLBACK = "❌ Invalid callback data. Please try again."
    ERROR_PROCESSING_SELECTION = "❌ An error occurred while processing your selection. Please try again."
    ERROR_PROCESSING_CALLBACK = "❌ Error processing selection"
    
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.translator = FreeTranslator()
        self.db = DatabaseManager()
        self.voice_transcriber = VoiceTranscriber()
        
        # State management for two-step language selection is now handled by database
        
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        
        logger.info("TelegramBot initialized with database and voice transcription")
    
    def answer_callback_query(self, callback_query_id: str, text: str = None) -> bool:
        """Answer callback query to remove loading state"""
        try:
            url = f"{self.base_url}/answerCallbackQuery"
            payload = {
                'callback_query_id': callback_query_id
            }
            if text:
                payload['text'] = text
            
            response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
            return response.status_code == 200
            
        except (requests.RequestException, requests.Timeout) as e:
            logger.error(f"Failed to answer callback query: {e}")
            return False
    
    def send_message(self, chat_id: int, text: str, parse_mode: str = 'Markdown') -> bool:
        """Send message to Telegram chat"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
            return response.status_code == 200
            
        except (requests.RequestException, requests.Timeout) as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def delete_message(self, chat_id: int, message_id: int) -> bool:
        """Delete message from Telegram chat"""
        try:
            url = f"{self.base_url}/deleteMessage"
            payload = {
                'chat_id': chat_id,
                'message_id': message_id
            }
            
            logger.info(f"Attempting to delete message {message_id} in chat {chat_id}")
            response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
            result = response.json()
            
            if response.status_code == 200:
                logger.info(f"Successfully deleted message {message_id} in chat {chat_id}")
                return True
            else:
                logger.error(f"Failed to delete message {message_id} in chat {chat_id}: {result}")
                return False
            
        except (requests.RequestException, requests.Timeout) as e:
            logger.error(f"Failed to delete message {message_id} in chat {chat_id}: {e}")
            return False
    
    def send_keyboard(self, chat_id: int, text: str, keyboard: List[List]) -> bool:
        """Send message with inline keyboard"""
        try:
            url = f"{self.base_url}/sendMessage"
            
            # Create inline keyboard
            inline_keyboard = []
            for row in keyboard:
                inline_row = []
                for button in row:
                    if isinstance(button, tuple):
                        # New format: (display_text, callback_data)
                        display_text, callback_data = button
                    else:
                        # Legacy format: just text
                        display_text = button
                        callback_data = button.lower()
                    
                    inline_row.append({
                        'text': display_text,
                        'callback_data': callback_data
                    })
                inline_keyboard.append(inline_row)
            
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'Markdown',
                'reply_markup': {
                    'inline_keyboard': inline_keyboard
                }
            }
            
            response = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
            return response.status_code == 200
            
        except (requests.RequestException, requests.Timeout) as e:
            logger.error(f"Failed to send keyboard: {e}")
            return False
    
    def get_user_language_pair(self, chat_id: int) -> Tuple[str, str]:
        """Get chat's language pair from database"""
        logger.info(f"Retrieving language preferences for chat {chat_id}")
        prefs = self.db.get_user_preferences(chat_id)
        if prefs:
            logger.info(f"Chat {chat_id} has language pair {prefs[0]}-{prefs[1]}")
            return prefs
        else:
            # Default fallback
            default_pair = ('en', 'ru')
            logger.info(f"Chat {chat_id} has no preferences, using default: {default_pair[0]}-{default_pair[1]}")
            return default_pair
    
    def set_user_language_pair(self, chat_id: int, lang1: str, lang2: str) -> bool:
        """Set chat's language pair in database"""
        if (LanguageDetector.is_valid_language(lang1) and 
            LanguageDetector.is_valid_language(lang2) and 
            lang1 != lang2):
            
            success = self.db.set_user_preferences(chat_id, lang1, lang2)
            if success:
                logger.info(f"Language pair set to {lang1} and {lang2} in chat {chat_id}")
                return True
            else:
                logger.error(f"Failed to save language pair to database for chat {chat_id}")
                return False
        else:
            logger.warning(f"Invalid language pair {lang1} and {lang2} for chat {chat_id}")
            return False
    
    def update_user_stats(self, user_id: int) -> bool:
        """Update user translation statistics in database"""
        return self.db.update_user_stats(user_id)
    
    def _create_language_keyboard(self, exclude_lang: str = None) -> List[List[tuple]]:
        """Create keyboard with all available languages"""
        languages = list(LanguageDetector.SUPPORTED_LANGUAGES.items())
        
        # Filter out excluded language if specified
        if exclude_lang:
            languages = [(code, name) for code, name in languages if code != exclude_lang]
        
        # Create keyboard with 3 languages per row
        keyboard = []
        row = []
        for code, name in languages:
            # Create button text with flag emoji and language name
            flag_emoji = self._get_language_flag(code)
            button_text = f"{flag_emoji} {name}"
            row.append((button_text, code))  # (display_text, callback_data)
            
            if len(row) == 3:
                keyboard.append(row)
                row = []
        
        # Add remaining languages
        if row:
            keyboard.append(row)
        
        return keyboard
    
    def _get_language_flag(self, lang_code: str) -> str:
        """Get flag emoji for language code"""
        flag_map = {
            'th': '\U0001F1F9\U0001F1ED', 'ru': '\U0001F1F7\U0001F1FA', 'zh': '\U0001F1E8\U0001F1F3', 'en': '\U0001F1FA\U0001F1F8', 'es': '\U0001F1EA\U0001F1F8', 'fr': '\U0001F1EB\U0001F1F7',
            'de': '\U0001F1E9\U0001F1EA', 'it': '\U0001F1EE\U0001F1F9', 'ja': '\U0001F1EF\U0001F1F5', 'ko': '\U0001F1F0\U0001F1F7', 'ar': '\U0001F1F8\U0001F1E6', 'hi': '\U0001F1EE\U0001F1F3',
            'pl': '\U0001F1F5\U0001F1F1', 'cs': '\U0001F1E8\U0001F1FF', 'nl': '\U0001F1F3\U0001F1F1', 'sv': '\U0001F1F8\U0001F1EA', 'pt': '\U0001F1F5\U0001F1F9', 'tr': '\U0001F1F9\U0001F1F7',
            'da': '\U0001F1E9\U0001F1F0', 'no': '\U0001F1F3\U0001F1F4', 'fi': '\U0001F1EB\U0001F1EE', 'el': '\U0001F1EC\U0001F1F7', 'he': '\U0001F1EE\U0001F1F1', 'vi': '\U0001F1FB\U0001F1F3',
            'id': '\U0001F1EE\U0001F1E9', 'ms': '\U0001F1F2\U0001F1FE', 'tl': '\U0001F1F5\U0001F1ED', 'uk': '\U0001F1FA\U0001F1E6', 'sk': '\U0001F1F8\U0001F1F0', 'hu': '\U0001F1ED\U0001F1FA',
            'ro': '\U0001F1F7\U0001F1F4', 'bg': '\U0001F1E7\U0001F1EC', 'hr': '\U0001F1ED\U0001F1F7', 'sr': '\U0001F1F7\U0001F1F8', 'sl': '\U0001F1F8\U0001F1EE', 'et': '\U0001F1EA\U0001F1EA',
            'lv': '\U0001F1F1\U0001F1FB', 'lt': '\U0001F1F1\U0001F1F9', 'fa': '\U0001F1EE\U0001F1F7', 'ur': '\U0001F1F5\U0001F1F0', 'bn': '\U0001F1E7\U0001F1E9', 'ta': '\U0001F1EE\U0001F1F3',
            'te': '\U0001F1EE\U0001F1F3', 'mr': '\U0001F1EE\U0001F1F3', 'gu': '\U0001F1EE\U0001F1F3', 'kn': '\U0001F1EE\U0001F1F3', 'ml': '\U0001F1EE\U0001F1F3', 'si': '\U0001F1F1\U0001F1F0'
        }
        return flag_map.get(lang_code, '🌍')
    
    def _get_language_code_from_button(self, button_text: str) -> str | None:
        """Extract language code from button text"""
        # Remove flag emoji and get language name
        parts = button_text.split(' ', 1)
        if len(parts) != 2:
            return None
        
        lang_name = parts[1]
        
        # Find language code by name
        for code, name in LanguageDetector.SUPPORTED_LANGUAGES.items():
            if name == lang_name:
                return code
        
        return None
    
    def process_message(self, update: Dict) -> None:
        """Process incoming Telegram message"""
        try:
            if 'message' in update:
                self._handle_message(update['message'])
            elif 'edited_message' in update:
                self._handle_edited_message(update['edited_message'])
            elif 'callback_query' in update:
                self._handle_callback_query(update['callback_query'])
                
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error processing update: {e}")
    
    def _handle_message(self, message: Dict) -> None:
        """Handle text and voice messages"""
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        user_name = message['from'].get('first_name', 'User')
        
        # Handle voice messages first
        if 'voice' in message:
            self._handle_voice_message(message, chat_id, user_id, user_name)
            return
        
        # Handle text messages
        text = message.get('text', '').strip()
        if not text:
            return
        
        # Handle commands
        if text.startswith('/'):
            self._handle_command(chat_id, user_id, text)
            return
        
        # Regular text message - translate it
        self._handle_text_message(message, chat_id, user_id, user_name, text)
    
    def _handle_voice_message(self, message: Dict, chat_id: int, user_id: int, user_name: str) -> None:
        """Handle voice message transcription and translation with intelligent fallback strategy"""
        try:
            voice = message['voice']
            file_id = voice['file_id']
            duration = voice.get('duration', 0)
            
            logger.info(f"Processing voice message from {user_name} (duration: {duration}s)")
            
            # Step 1: Get language pair for user
            lang1, lang2 = self.get_user_language_pair(chat_id)
            has_language_pair = bool(lang1 and lang2)
            
            # Step 2: Transcribe with intelligent fallback strategy
            transcription_result = self._transcribe_with_fallback(file_id)
            
            if not transcription_result:
                self._send_transcription_error(chat_id, user_name)
                return
            
            transcription, detected_lang = transcription_result
            
            # Step 3: Handle case where no language pair is set
            if not has_language_pair:
                response = f"🎤 *Voice Transcription*\n\n👤 **{user_name}:**\n📝 **Transcription:**\n_{transcription}_"
                if detected_lang:
                    response += f"\n\n🌍 **Detected Language:** {LanguageDetector.SUPPORTED_LANGUAGES.get(detected_lang, detected_lang)}"
                self.send_message(chat_id, response)
                return
            
            # Step 4: Determine target language based on detected language and language pair
            target_lang = self._determine_target_language(detected_lang, lang1, lang2)
            if not target_lang:
                # Detected language is not in the pair, show transcription only
                logger.warning(f"Probably cound't detect language correctly from user {user_name}, sending transcription only")
                response = f"🎤 *Voice Transcription*\n\n👤 **{user_name}:**\n📝 **Transcription:**\n_{transcription}_"
                if detected_lang:
                    response += f"\n\n🌍 **Detected Language:** {LanguageDetector.SUPPORTED_LANGUAGES.get(detected_lang, detected_lang)}"
                response += f"\n\n💡 **Tip:** Use /setpair to configure languages for automatic translation."
                self.send_message(chat_id, response)
                return
            
            # Step 5: Don't translate if already in target language
            if detected_lang == target_lang:
                response = f"✅ *Already in {LanguageDetector.SUPPORTED_LANGUAGES.get(target_lang, target_lang)}*\n\n👤 **{user_name}:**\n_{transcription}_"
                logger.info(f"Voice already in target language, sending formatted response for chat {chat_id}")
                self.send_message(chat_id, response)
                return
            
            # Step 6: Translate the transcription
            translated = self.translator.translate_text(transcription, target_lang, detected_lang)
            
            if translated and translated != transcription:
                self.update_user_stats(user_id)
                
                # Store the translation
                message_id = message.get('message_id')
                if message_id:
                    self.db.store_message_translation(
                        chat_id, message_id, user_id, transcription, translated,
                        detected_lang, target_lang
                    )
                
                # Use same format as text messages
                response = f"🎤 *Voice Translation* ({detected_lang} → {target_lang})\n\n"
                response += f"👤 **{user_name}:**\n"
                response += f"_{transcription}_\n\n"
                response += "🔄 **Translation:**\n"
                response += f"_{translated}_"
                
                logger.info(f"Voice translation successful, sending formatted response for chat {chat_id}")
                self.send_message(chat_id, response)
            else:
                self._send_translation_error(chat_id, user_name, transcription)
                
        except (OSError, ImportError, AttributeError, ValueError, requests.RequestException) as e:
            logger.error(f"Error processing voice message: {e}")
            error_msg = f"❌ *Voice processing error*\n\n👤 **{user_name}:**\n⚠️ **Error:** An unexpected error occurred while processing your voice message."
            self.send_message(chat_id, error_msg)
    
    def _transcribe_with_fallback(self, file_id: str) -> Optional[Tuple[str, Optional[str]]]:
        """Transcribe voice message with intelligent fallback strategy following the Python example pattern"""
        try:
            # Download the voice file
            audio_data = self.voice_transcriber._download_voice_file(file_id)
            if not audio_data:
                logger.error("Failed to download voice file")
                return None
            
            logger.info(f"Downloaded voice file, size: {len(audio_data)} bytes")
            
            # Save to temporary file for services that need file paths
            temp_audio_path = self.voice_transcriber._save_audio_to_temp_file(audio_data)
            if not temp_audio_path:
                logger.error("Failed to save audio to temp file")
                return None
            
            try:
                transcript = None
                detected_lang = None
                
                # Step 1: Try Whisper API first (best for Hebrew and many languages)
                if self.voice_transcriber.services_available.get('whisper', False):
                    logger.info("[INFO] Trying Whisper API transcription first...")
                    try:
                        transcript = self.voice_transcriber.whisper_transcriber.transcribe_audio(temp_audio_path)
                        if transcript:
                            logger.info("[SUCCESS] Whisper transcription successful")
                            # Try to detect language from the transcript
                            detected_lang = self.translator.detect_language(transcript)
                            return transcript, detected_lang
                    except Exception as e:
                        logger.warning(f"[WARN] Whisper failed: {e}")
                        logger.info("[INFO] Falling back to AssemblyAI...")
                
                # Step 2: Try AssemblyAI (good fallback)
                if self.voice_transcriber.services_available.get('assemblyai', False):
                    logger.info("[INFO] Trying AssemblyAI transcription...")
                    try:
                        transcript = self.voice_transcriber._transcribe_with_assemblyai(temp_audio_path)
                        if transcript:
                            logger.info("[SUCCESS] AssemblyAI transcription successful")
                            # Try to detect language from the transcript
                            detected_lang = self.translator.detect_language(transcript)
                            return transcript, detected_lang
                    except Exception as e:
                        logger.warning(f"[WARN] AssemblyAI failed: {e}")
                        logger.info("[INFO] Falling back to Google Speech-to-Text...")
                
                # Step 3: Try Google Speech-to-Text (final fallback)
                if self.voice_transcriber.services_available.get('google_speech', False):
                    logger.info("[INFO] Trying Google Speech-to-Text as final fallback...")
                    try:
                        transcript = self._transcribe_with_google_speech(temp_audio_path, None)  # None for auto-detection
                        if transcript:
                            logger.info("[SUCCESS] Google transcription successful")
                            # Try to detect language from the transcript
                            detected_lang = self.translator.detect_language(transcript)
                            return transcript, detected_lang
                    except (GoogleAPICallError, ResourceExhausted) as e:
                        logger.warning(f"[WARN] Google API failed: {e}")
                    except Exception as e:
                        logger.warning(f"[WARN] Google Speech unexpected error: {e}")
                
                logger.error("[FATAL] All transcription services failed")
                return None
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_audio_path)
                except (OSError, ImportError, AttributeError, ValueError) as e:
                    logger.warning(f"Failed to clean up temp file: {e}")
                    
        except Exception as e:
            logger.error(f"Error in transcription fallback: {e}")
            return None
    

    
    def _transcribe_with_google_speech(self, audio_path: str, language_code: Optional[str] = None) -> Optional[str]:
        """Full transcription using Google Speech-to-Text with optional language specification"""
        try:
            self.voice_transcriber._respect_rate_limit('google_speech')
            
            # Create credentials from JSON if available
            credentials = None
            if self.voice_transcriber.google_credentials_json:
                import json
                from google.oauth2 import service_account
                try:
                    logger.info(f"[DEBUG] Google credentials JSON length: {len(self.voice_transcriber.google_credentials_json)}")
                    logger.info(f"[DEBUG] Google credentials JSON preview: {self.voice_transcriber.google_credentials_json[:100]}...")
                    
                    # Check if JSON is empty or just whitespace
                    if not self.voice_transcriber.google_credentials_json.strip():
                        logger.error("[ERROR] Google credentials JSON is empty or contains only whitespace")
                        raise ValueError("Empty Google credentials JSON")
                    
                    credentials_info = json.loads(self.voice_transcriber.google_credentials_json)
                    credentials = service_account.Credentials.from_service_account_info(credentials_info)
                    logger.info("[DEBUG] Successfully created Google credentials from JSON")
                except json.JSONDecodeError as e:
                    logger.error(f"[ERROR] Failed to parse Google credentials JSON: {e}")
                    logger.error(f"[ERROR] JSON content (first 200 chars): {self.voice_transcriber.google_credentials_json[:200]}")
                    logger.error("[ERROR] Please ensure GOOGLE_APPLICATION_CREDENTIALS_JSON contains valid JSON")
                except ValueError as e:
                    logger.error(f"[ERROR] Google credentials validation failed: {e}")
                except Exception as e:
                    logger.error(f"[ERROR] Failed to create Google credentials: {e}")
            else:
                logger.warning("[WARN] No Google credentials JSON available - GOOGLE_APPLICATION_CREDENTIALS_JSON not set")
            
            # Create client with credentials
            if credentials:
                client = speech.SpeechClient(credentials=credentials)
            else:
                client = speech.SpeechClient()
            
            with open(audio_path, "rb") as f:
                content = f.read()
            
            audio = speech.RecognitionAudio(content=content)
            
            # Configure based on whether we have a detected language
            if language_code:
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                    sample_rate_hertz=48000,  # Telegram voice messages are typically 48kHz
                    language_code=language_code,
                    enable_automatic_punctuation=True
                )
            else:
                # Use auto language detection with multiple language hints
                # Extended list including Hebrew and other languages
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                    sample_rate_hertz=48000,
                    language_code="en-US",  # Primary language hint
                    alternative_language_codes=[
                        "es-ES", "fr-FR", "de-DE", "it-IT", "pt-BR", "ru-RU", 
                        "ja-JP", "ko-KR", "zh-CN", "he-IL", "ar-SA", "hi-IN",
                        "tr-TR", "pl-PL", "nl-NL", "sv-SE", "da-DK", "no-NO",
                        "fi-FI", "cs-CZ", "sk-SK", "hu-HU", "ro-RO", "bg-BG",
                        "hr-HR", "sl-SI", "et-EE", "lv-LV", "lt-LT", "mt-MT"
                    ],
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
                
        except Exception as e:
            logger.error(f"[ERROR] Google Speech transcription failed: {e}")
            return None
    
    def _determine_target_language(self, detected_lang: Optional[str], lang1: str, lang2: str) -> Optional[str]:
        """Determine target language based on detected language and user's language pair"""
        if not detected_lang:
            logger.info("No language detected, cannot determine target language")
            return None
        
        # Detect language using translator if not already detected
        if detected_lang == 'unknown':
            detected_lang = self.translator.detect_language(detected_lang, allowed_langs=(lang1, lang2))
        
        logger.info(f"Determining target language for detected '{detected_lang}' with pair ({lang1}, {lang2})")
        
        # Determine target language based on detected language and language pair
        if detected_lang == lang1:
            target_lang = lang2
            logger.info(f"Translating voice {lang1} -> {lang2}")
            return target_lang
        elif detected_lang == lang2:
            target_lang = lang1
            logger.info(f"Translating voice {lang2} -> {lang1}")
            return target_lang
        else:
            # Detected language is neither of the pair
            logger.info(f"Detected language '{detected_lang}' not in pair ({lang1}, {lang2}), ignoring voice translation")
            return None
    
    def _send_transcription_error(self, chat_id: int, user_name: str) -> None:
        """Send transcription error message"""
        error_msg = f"❌ *Voice transcription failed*\n\n👤 **{user_name}:**\n⚠️ **Error:** Unable to transcribe this voice message.\n\n"
        error_msg += "🔧 **Possible reasons:**\n"
        error_msg += "• Audio quality is too low\n"
        error_msg += "• No speech detected\n"
        error_msg += "• All transcription services are temporarily unavailable\n\n"
        error_msg += "💡 **Tip:** Try sending a text message instead."
        self.send_message(chat_id, error_msg)
    
    def _send_translation_error(self, chat_id: int, user_name: str, transcription: str) -> None:
        """Send translation error message"""
        error_response = "❌ *Voice translation failed*\n\n"
        error_response += f"👤 **{user_name}:**\n"
        error_response += f"_{transcription}_\n\n"
        error_response += "⚠️ **Error:** Unable to translate this voice message. Please try again."
        logger.info(f"Voice translation failed, sending error response for chat {chat_id}")
        self.send_message(chat_id, error_response)
    
    def _handle_text_message(self, message: Dict, chat_id: int, user_id: int, user_name: str, text: str) -> None:
        """Handle regular text message translation"""
        # Get user language pair
        lang1, lang2 = self.get_user_language_pair(chat_id)
        logger.info(f"Chat {chat_id} has language pair {lang1}-{lang2}")
        detected_lang = self.translator.detect_language(text, allowed_langs=(lang1, lang2))
        logger.info(f"Detected language for text '{text[:20]}...': {detected_lang}")
        
        # Determine target language based on detected language and language pair
        if detected_lang == lang1:
            target_lang = lang2
            logger.info(f"Translating {lang1} -> {lang2}")
        elif detected_lang == lang2:
            target_lang = lang1
            logger.info(f"Translating {lang2} -> {lang1}")
        else:
            # Ignore translation if detected language is neither of the pair
            logger.warning(f"Detected language '{detected_lang}' not in pair ({lang1}, {lang2}), ignoring translation")
            return
        
        # Don't translate if already in target language
        if detected_lang == target_lang:
            response = f"✅ *Already in {LanguageDetector.SUPPORTED_LANGUAGES.get(target_lang, target_lang)}*\n\n👤 **{user_name}:**\n_{text}_"
            logger.info(f"Already in target language, sending formatted response for chat {chat_id}")
            self.send_message(chat_id, response)
            return
        
        # Translate the message
        translated = self.translator.translate_text(text, target_lang, detected_lang)
        
        if translated and translated != text:
            self.update_user_stats(user_id)
            
            # Store the translation for potential future edits
            message_id = message.get('message_id')
            if message_id:
                self.db.store_message_translation(
                    chat_id, message_id, user_id, text, translated,
                    detected_lang, target_lang
                )
            
            response = f"🔤 *Translation* ({detected_lang} → {target_lang})\n\n"
            response += f"👤 **{user_name}:**\n"
            response += f"_{text}_\n\n"
            response += "🔄 **Translation:**\n"
            response += f"_{translated}_"
            
            logger.info(f"Translation successful, sending formatted response for chat {chat_id}")
            self.send_message(chat_id, response)
        else:
            error_response = "❌ *Translation failed*\n\n"
            error_response += f"👤 **{user_name}:**\n"
            error_response += f"_{text}_\n\n"
            error_response += "⚠️ **Error:** Unable to translate this text. Please try again."
            logger.info(f"Translation failed, sending error response for chat {chat_id}")
            self.send_message(chat_id, error_response)
    
    def _handle_callback_query(self, callback_query: Dict) -> None:
        """Handle inline keyboard callback"""
        try:
            chat_id = callback_query['message']['chat']['id']
            data = callback_query['data']
            callback_query_id = callback_query['id']
            
            logger.info(f"Processing callback query for chat {chat_id} with data: {data}")
            
            # Answer the callback query immediately to remove loading state
            self.answer_callback_query(callback_query_id)
            
            # Check if chat has language selection state in database
            state = self.db.get_language_selection_state(chat_id)
            if state:
                logger.info(f"Found language selection state for chat {chat_id}: {state}")
                self._handle_language_selection(chat_id, data)
            # Handle legacy language pair selection (for backward compatibility)
            elif '|' in data:  # Format: "flag1|flag2"
                logger.info(f"Handling legacy language selection for chat {chat_id}")
                self._handle_legacy_language_selection(chat_id, data)
            else:
                logger.warning(f"Unknown callback data format for chat {chat_id}: {data}")
                logger.warning(f"Chat {chat_id} not in language selection state")
                self.send_message(chat_id, self.ERROR_INVALID_CALLBACK)
                
        except SystemExit:
            raise
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error handling callback query: {e}")
            # Try to answer callback query and send error message if we can extract chat_id
            try:
                callback_query_id = callback_query.get('id')
                if callback_query_id:
                    self.answer_callback_query(callback_query_id, self.ERROR_PROCESSING_CALLBACK)
                
                chat_id = callback_query.get('message', {}).get('chat', {}).get('id')
                if chat_id:
                    self.send_message(chat_id, self.ERROR_PROCESSING_SELECTION)
            except (KeyError, ValueError, TypeError):
                pass
    
    def _handle_edited_message(self, message: Dict) -> None:
        """Handle edited message and show previous translation"""
        try:
            chat_id = message['chat']['id']
            user_id = message['from']['id']
            message_id = message['message_id']
            text = message.get('text', '').strip()
            
            if not text:
                return
            
            # Handle commands in edited messages
            if text.startswith('/'):
                self._handle_command(chat_id, user_id, text)
                return
            
            # Get previous translation for this message
            previous_translation = self.db.get_message_translation(chat_id, message_id)
            
            if previous_translation:
                self._handle_edited_message_with_previous_translation(
                    message, chat_id, user_id, message_id, text, previous_translation
                )
            else:
                # No previous translation found, treat as new message
                logger.info(f"No previous translation found for edited message {message_id} in chat {chat_id}")
                self._handle_message(message)
                
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error handling edited message: {e}")
    
    def _handle_edited_message_with_previous_translation(self, message: Dict, chat_id: int, 
                                                        user_id: int, message_id: int, 
                                                        text: str, previous_translation: Dict) -> None:
        """Handle edited message when previous translation exists"""
        user_name = message['from'].get('first_name', 'User')
        response = self._build_edit_response_header(user_name, text, previous_translation)
        
        # Get new translation
        target_lang = self._get_target_language_for_edit(chat_id, text)
        if not target_lang:
            response += "⚠️ **Note:** New text language not in your language pair"
            self.send_message(chat_id, response)
            return
        
        detected_lang = self.translator.detect_language(text, allowed_langs=(lang1, lang2))
        response += self._build_new_translation_response(
            text, detected_lang, target_lang, chat_id, message_id, user_id
        )
        
        self.send_message(chat_id, response)
    
    def _build_edit_response_header(self, user_name: str, text: str, previous_translation: Dict) -> str:
        """Build the header part of edit response with previous translation"""
        response = "✏️ *Message Edited*\n\n"
        response += f"👤 **{user_name}:**\n"
        response += f"_{text}_\n\n"
        response += "📝 **Previous Translation:**\n"
        response += f"_{previous_translation['translated_text']}_\n\n"
        return response
    
    def _get_target_language_for_edit(self, chat_id: int, text: str) -> str | None:
        """Get target language for edited message"""
        lang1, lang2 = self.get_user_language_pair(chat_id)
        detected_lang = self.translator.detect_language(text, allowed_langs=(lang1, lang2))
        
        if detected_lang == lang1:
            return lang2
        elif detected_lang == lang2:
            return lang1
        return None
    
    def _build_new_translation_response(self, text: str, detected_lang: str, target_lang: str,
                                       chat_id: int, message_id: int, user_id: int) -> str:
        """Build response for new translation of edited message"""
        if detected_lang == target_lang:
            return "✅ **New text already in target language**"
        
        new_translated = self.translator.translate_text(text, target_lang, detected_lang)
        if new_translated and new_translated != text:
            # Store the new translation
            self.db.store_message_translation(
                chat_id, message_id, user_id, text, new_translated,
                detected_lang, target_lang
            )
            return f"🔄 **New Translation:**\n_{new_translated}_"
        else:
            return "❌ **New translation failed**"
    
    def _handle_language_selection(self, chat_id: int, data: str) -> None:
        """Handle two-step language selection process"""
        error_message = self.ERROR_USE_SETPAIR
        invalid_selection_message = self.ERROR_INVALID_SELECTION
        invalid_state_message = self.ERROR_INVALID_STATE
        
        try:
            # Get state from database
            state = self.db.get_language_selection_state(chat_id)
            if not state:
                logger.warning(f"No selection state found for chat {chat_id}")
                self.send_message(chat_id, error_message)
                return
            
            selected_lang_code = self._extract_language_code(data)
            
            if not selected_lang_code:
                logger.warning(f"Invalid language selection for chat {chat_id}: {data}")
                self.send_message(chat_id, invalid_selection_message)
                return
            
            logger.info(f"Processing language selection for chat {chat_id}: {selected_lang_code} (step: {state['step']})")
            
            if state['step'] == 'first_lang':
                self._handle_first_language_selection(chat_id, selected_lang_code)
            elif state['step'] == 'second_lang':
                self._handle_second_language_selection(chat_id, selected_lang_code)
            else:
                logger.error(f"Invalid state step for chat {chat_id}: {state['step']}")
                self.send_message(chat_id, invalid_state_message)
                self.db.clear_language_selection_state(chat_id)
                
        except (OSError, ImportError, AttributeError, ValueError, requests.RequestException) as e:
            logger.error(f"Error in language selection for chat {chat_id}: {e}")
            self.send_message(chat_id, error_message)
            # Clean up the state to prevent further issues
            self.db.clear_language_selection_state(chat_id)
    
    def _extract_language_code(self, data: str) -> str | None:
        """Extract language code from callback data"""
        logger.info(f"Extracting language code from data: '{data}'")
        
        # First check if the data is already a valid language code
        if data in LanguageDetector.SUPPORTED_LANGUAGES:
            logger.info(f"Found direct language code: {data}")
            return data
        
        # If not, try to extract from button text format (for backward compatibility)
        extracted = self._get_language_code_from_button(data)
        logger.info(f"Extracted from button text: {extracted}")
        return extracted
    
    def _handle_first_language_selection(self, chat_id: int, selected_lang_code: str) -> None:
        """Handle first language selection in two-step process"""
        error_message = self.ERROR_USE_SETPAIR
        
        try:
            # Update state in database
            if not self.db.set_language_selection_state(chat_id, 'second_lang', selected_lang_code):
                logger.error(f"Failed to update selection state for chat {chat_id}")
                self.send_message(chat_id, error_message)
                return
            
            first_lang_name = LanguageDetector.SUPPORTED_LANGUAGES[selected_lang_code]
            first_flag = self._get_language_flag(selected_lang_code)
            
            keyboard = self._create_language_keyboard(exclude_lang=selected_lang_code)
            text = f"✅ *First language selected: {first_flag} {first_lang_name}*\n\nNow choose your second language:"
            
            logger.info(f"First language selected for chat {chat_id}: {selected_lang_code}")
            self.send_keyboard(chat_id, text, keyboard)
            
        except (OSError, ImportError, AttributeError, ValueError, requests.RequestException) as e:
            logger.error(f"Error in first language selection for chat {chat_id}: {e}")
            self.send_message(chat_id, error_message)
            self.db.clear_language_selection_state(chat_id)
    
    def _handle_second_language_selection(self, chat_id: int, selected_lang_code: str) -> None:
        """Handle second language selection in two-step process"""
        error_message = self.ERROR_USE_SETPAIR
        failed_message = self.ERROR_FAILED_SET_PAIR
        
        try:
            # Get current state from database
            state = self.db.get_language_selection_state(chat_id)
            if not state or not state.get('first_lang'):
                logger.error(f"No valid state found for chat {chat_id}")
                self.send_message(chat_id, error_message)
                self.db.clear_language_selection_state(chat_id)
                return
            
            first_lang = state['first_lang']
            second_lang = selected_lang_code
            
            logger.info(f"Second language selected for chat {chat_id}: {second_lang} (first was: {first_lang})")
            
            if self.set_user_language_pair(chat_id, first_lang, second_lang):
                self._send_language_pair_confirmation(chat_id, first_lang, second_lang)
            else:
                self.send_message(chat_id, failed_message)
            
            # Always clean up the state
            self.db.clear_language_selection_state(chat_id)
            logger.info(f"Language selection completed for chat {chat_id}")
            
        except (OSError, ImportError, AttributeError, ValueError, requests.RequestException) as e:
            logger.error(f"Error in second language selection for chat {chat_id}: {e}")
            self.send_message(chat_id, error_message)
            self.db.clear_language_selection_state(chat_id)
    
    def _send_language_pair_confirmation(self, chat_id: int, first_lang: str, second_lang: str) -> None:
        """Send confirmation message for language pair setup"""
        first_lang_name = LanguageDetector.SUPPORTED_LANGUAGES[first_lang]
        second_lang_name = LanguageDetector.SUPPORTED_LANGUAGES[second_lang]
        first_flag = self._get_language_flag(first_lang)
        second_flag = self._get_language_flag(second_lang)
        
        response = f"✅ *Language pair set to {first_flag} {first_lang_name} ↔ {second_flag} {second_lang_name}*\n\nNow send me any message and I'll translate between these languages!"
        self.send_message(chat_id, response)
    
    def _handle_legacy_language_selection(self, chat_id: int, data: str) -> None:
        """Handle legacy language pair selection format"""
        flag1, flag2 = data.split('|')
        lang1 = self._get_language_from_flag(flag1)
        lang2 = self._get_language_from_flag(flag2)
        
        if lang1 and lang2 and self.set_user_language_pair(chat_id, lang1, lang2):
            lang1_name = LanguageDetector.SUPPORTED_LANGUAGES[lang1]
            lang2_name = LanguageDetector.SUPPORTED_LANGUAGES[lang2]
            response = f"✅ *Language pair set to {lang1_name} ↔ {lang2_name}*\n\nNow send me any message and I'll translate between these languages!"
            self.send_message(chat_id, response)
    
    def _get_language_from_flag(self, flag: str) -> str | None:
        """Get language code from flag emoji"""
        flag_to_lang = {
            '\U0001F1F9\U0001F1ED': 'th',  # 🇹🇭
            '\U0001F1F7\U0001F1FA': 'ru',  # 🇷🇺
            '\U0001F1E8\U0001F1F3': 'zh',  # 🇨🇳
            '\U0001F1FA\U0001F1F8': 'en',  # 🇺🇸
            '\U0001F1EA\U0001F1F8': 'es',  # 🇪🇸
            '\U0001F1EB\U0001F1F7': 'fr',  # 🇫🇷
            '\U0001F1E9\U0001F1EA': 'de',  # 🇩🇪
            '\U0001F1EE\U0001F1F9': 'it',  # 🇮🇹
            '\U0001F1EF\U0001F1F5': 'ja',  # 🇯🇵
            '\U0001F1F0\U0001F1F7': 'ko',  # 🇰🇷
            '\U0001F1F8\U0001F1E6': 'ar',  # 🇸🇦
            '\U0001F1EE\U0001F1F3': 'hi',  # 🇮🇳
            '\U0001F1F5\U0001F1F1': 'pl',  # 🇵🇱
            '\U0001F1E8\U0001F1FF': 'cs',  # 🇨🇿
            '\U0001F1F3\U0001F1F1': 'nl',  # 🇳🇱
            '\U0001F1F8\U0001F1EA': 'sv',  # 🇸🇪
            '\U0001F1F5\U0001F1F9': 'pt',  # 🇵🇹
            '\U0001F1F9\U0001F1F7': 'tr',  # 🇹🇷
            '\U0001F1E9\U0001F1F0': 'da',  # 🇩🇰
            '\U0001F1F3\U0001F1F4': 'no',  # 🇳🇴
            '\U0001F1EB\U0001F1EE': 'fi',  # 🇫🇮
            '\U0001F1EC\U0001F1F7': 'el',  # 🇬🇷
            '\U0001F1EE\U0001F1F1': 'he',  # 🇮🇱
            '\U0001F1FB\U0001F1F3': 'vi',  # 🇻🇳
            '\U0001F1EE\U0001F1E9': 'id',  # 🇮🇩
            '\U0001F1F2\U0001F1FE': 'ms',  # 🇲🇾
            '\U0001F1F5\U0001F1ED': 'tl',  # 🇵🇭
            '\U0001F1FA\U0001F1E6': 'uk',  # 🇺🇦
            '\U0001F1F8\U0001F1F0': 'sk',  # 🇸🇰
            '\U0001F1ED\U0001F1FA': 'hu',  # 🇭🇺
            '\U0001F1F7\U0001F1F4': 'ro',  # 🇷🇴
            '\U0001F1E7\U0001F1EC': 'bg',  # 🇧🇬
            '\U0001F1ED\U0001F1F7': 'hr',  # 🇭🇷
            '\U0001F1F7\U0001F1F8': 'sr',  # 🇷🇸
            '\U0001F1F8\U0001F1EE': 'sl',  # 🇸🇮
            '\U0001F1EA\U0001F1EA': 'et',  # 🇪🇪
            '\U0001F1F1\U0001F1FB': 'lv',  # 🇱🇻
            '\U0001F1F1\U0001F1F9': 'lt',  # 🇱🇹
            '\U0001F1EE\U0001F1F7': 'fa',  # 🇮🇷
            '\U0001F1F5\U0001F1F0': 'ur',  # 🇵🇰
            '\U0001F1E7\U0001F1E9': 'bn',  # 🇧🇩
            '\U0001F1F1\U0001F1F0': 'si'   # 🇱🇰
        }
        return flag_to_lang.get(flag)
    
    def _handle_command(self, chat_id: int, user_id: int, command: str) -> None:
        """Handle bot commands"""
        cmd_parts = command.split()
        cmd = cmd_parts[0].lower()
        cmd = cmd.split('@')[0]  # removes @MyLangBuddy_bot if present
        
        if cmd == '/start':
            welcome_text = """
🤖 *Welcome to Language Buddy Bot!*

I help you communicate between two languages! Set up your language pair once and I'll translate messages bidirectionally.

*Commands:*
/setpair - Choose your language pair
/stats - View your translation statistics
/help - Show help information
/languages - List all supported languages

*Quick Start:*
1. Use /setpair to choose your two languages
2. Send me any text message
3. I'll translate between your languages automatically!

*Group Chat Support:*
• Language pairs are saved per chat
• Works in both private and group chats
• Each group maintains its own language pair

_Just send me a message to get started!_ 🚀
            """
            self.send_message(chat_id, welcome_text)
            
        elif cmd == '/help':
            help_text = """
🆘 *Language Buddy Bot Help*

*How it works:*
• Set up a language pair (e.g., Thai ↔ Russian)
• Send any text message and I'll translate between your languages
• I auto-detect which language you're using
• Works bidirectionally - no need to specify direction

*Commands:*
• `/start` - Welcome message
• `/setpair` - Choose your language pair
• `/stats` - View your translation statistics
• `/languages` - List all supported languages
• `/help` - Show this help

*Pro Tips:*
• Set your language pair once with /setpair
• I support 40+ languages
• Works with any text length
• Free and unlimited!
• Works in both private and group chats

_Need help? Just ask!_ 💬
            """
            self.send_message(chat_id, help_text)
            
        elif cmd == '/setpair':
            # Clean up any existing stale state for this chat
            self.db.clear_language_selection_state(chat_id)
            
            # Start two-step language selection process
            if not self.db.set_language_selection_state(chat_id, 'first_lang'):
                logger.error(f"Failed to set initial selection state for chat {chat_id}")
                self.send_message(chat_id, "❌ Failed to start language selection. Please try again.")
                return
            
            logger.info(f"Started language selection for chat {chat_id}")
            
            # Create keyboard with all available languages
            keyboard = self._create_language_keyboard()
            
            text = "🌍 *Step 1: Choose your first language*\n\nSelect the first language for your translation pair:"
            self.send_keyboard(chat_id, text, keyboard)
            
        elif cmd == '/languages':
            lang_list = LanguageDetector.get_language_list()
            response = f"🌍 *Supported Languages:*\n\n```\n{lang_list}\n```\n\nUse `/setpair` to choose your language pair!"
            self.send_message(chat_id, response)
            
        elif cmd == '/stats':
            stats = self.db.get_user_stats(user_id) or {'translations': 0, 'joined': 'Unknown'}
            current_pair = self.get_user_language_pair(chat_id)
            logger.info(f"Chat {chat_id} has language pair {current_pair[0]}-{current_pair[1]}")
            lang1_name = LanguageDetector.SUPPORTED_LANGUAGES.get(current_pair[0], current_pair[0])
            lang2_name = LanguageDetector.SUPPORTED_LANGUAGES.get(current_pair[1], current_pair[1])
            
            response = f"""
📊 *Your Translation Stats:*

🔤 **Translations:** {stats['translations']}
🌍 **Language Pair:** {lang1_name} ↔ {lang2_name}
📅 **Member Since:** {stats.get('joined', 'Unknown')}

_Keep translating to increase your stats!_ 🚀
            """
            self.send_message(chat_id, response)
            
        else:
            self.send_message(chat_id, "❓ Unknown command. Use /help to see available commands.") 