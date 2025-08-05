import logging
from typing import Optional

logger = logging.getLogger(__name__)

class FreeTranslator:
    """Free translation using Google Translate"""
    
    def __init__(self):
        # initialization of the translator
        pass
    
    def translate_text(self, text: str, target_lang: str, source_lang: str = 'auto') -> Optional[str]:
        """Translate text using Google Translate"""
        
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
            
            if source_lang == 'auto':
                result = translator.translate(clean_text, dest=target_lang)
            else:
                result = translator.translate(clean_text, src=source_lang, dest=target_lang)
            
            translated_text = result.text
            logger.info(f"Google Translate result: {translated_text[:100]}...")
            
            # Check if translation is meaningful
            if not translated_text or translated_text == clean_text:
                logger.warning("Google Translate returned empty or unchanged text")
                return None
            
            # Check if translation was cut off (common issue with googletrans)
            if len(translated_text) < len(clean_text) * 0.3:  # Too short
                logger.warning("Google Translate result seems too short, might be cut off")
                return None
                
            return translated_text
            
        except Exception as e:
            logger.error(f"Google Translate failed: {e}")
            return None
    
    def detect_language(self, text: str) -> str:
        """Detect language of text"""
        try:
            from googletrans import Translator
            translator = Translator()
            detection = translator.detect(text)
            return detection.lang
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return 'unknown' 