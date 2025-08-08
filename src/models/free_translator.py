import logging
import asyncio
import requests
from typing import Optional

logger = logging.getLogger(__name__)

class FreeTranslator:
    """Free translation using Google Translate"""
    
    def __init__(self):
        # initialization of the translator
        pass
    
    def translate_text(self, text: str, target_lang: str, source_lang: str = 'auto') -> Optional[str]:
        """Translate text using Google Translate"""
        
        if not text or not isinstance(text, str):
            logger.error("Invalid text input for translation")
            return "❌ Translation failed - please try again"
        
        logger.info(f"Translating text: {text[:50]}... from {source_lang} to {target_lang}")
        
        result = self._translate_googletrans(text, target_lang, source_lang)
        
        if result is None:
            logger.error("❌ Translation failed")
            return "❌ Translation failed - please try again"
        else:
            logger.info("✅ Translation completed successfully")
            
        return result
    
    def _translate_googletrans(self, text: str, target_lang: str, source_lang: str) -> Optional[str]:
        """Translate using Google Translate (free library)"""
        try:
            from googletrans import Translator
            translator = Translator()
            
            logger.info(f"Google Translate: {source_lang} -> {target_lang}, text length: {len(text)}")
            
            # Clean text - remove extra whitespace
            clean_text = ' '.join(text.split())
            
            # Run the async translation
            if source_lang == 'auto':
                result = asyncio.run(translator.translate(clean_text, dest=target_lang))
            else:
                result = asyncio.run(translator.translate(clean_text, src=source_lang, dest=target_lang))
            
            translated_text = result.text
            logger.info(f"Google Translate result: {translated_text[:100]}...")
            
            # Check if translation is meaningful
            if not translated_text or translated_text == clean_text:
                logger.warning("Google Translate returned empty or unchanged text")
                return None
            
            # Check if translation was cut off (common issue with googletrans)
            # Only check for very short results that might indicate truncation
            if len(translated_text) < 3:  # Too short to be meaningful
                logger.warning("Google Translate result seems too short, might be cut off")
                return None
                
            return translated_text
            
        except (OSError, ImportError, AttributeError, ValueError, requests.RequestException) as e:
            logger.error(f"Google Translate failed: {e}")
            return None
    
    def detect_language(self, text: str) -> str:
        """Detect language of text"""
        try:
            from googletrans import Translator
            translator = Translator()
            
            # Run the async detection
            detection = asyncio.run(translator.detect(text))
            detected_code = detection.lang
            
            # Map googletrans language codes to our supported codes
            code_mapping = {
                'iw': 'he',  # googletrans returns 'iw' for Hebrew
                'zh-cn': 'zh',  # Simplified Chinese
                'zh-tw': 'zh',  # Traditional Chinese
                'zh-hk': 'zh',  # Hong Kong Chinese
                'zh-sg': 'zh',  # Singapore Chinese
            }
            
            # Convert to our supported code if mapping exists
            mapped_code = code_mapping.get(detected_code, detected_code)
            
            # Special handling for Hebrew detection
            if detected_code == 'hi' and self._contains_hebrew_characters(text):
                mapped_code = 'he'
                logger.info(f"✅ Hebrew text incorrectly detected as Hindi, corrected to Hebrew")
            
            logger.info(f"googletrans detected '{detected_code}', mapped to '{mapped_code}'")
            
            if detected_code != mapped_code:
                logger.info(f"✅ Language code mapped: {detected_code} → {mapped_code}")
            else:
                logger.info(f"ℹ️  No mapping needed for: {detected_code}")
            
            return mapped_code
        except (OSError, ImportError, AttributeError, ValueError, requests.RequestException) as e:
            logger.error(f"Language detection failed: {e}")
            return 'unknown'
    
    def _contains_hebrew_characters(self, text: str) -> bool:
        """Check if text contains Hebrew characters"""
        # Hebrew Unicode range: U+0590 to U+05FF
        hebrew_range = range(0x0590, 0x0600)
        
        for char in text:
            if ord(char) in hebrew_range:
                return True
        return False 