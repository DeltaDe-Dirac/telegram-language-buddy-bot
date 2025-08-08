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
            
            # Clean the text first
            clean_text = ' '.join(text.split())
            
            # Run the async detection
            detection = asyncio.run(translator.detect(clean_text))
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
            
            # Enhanced detection for transliterated text from voice transcription
            if self._is_likely_transliterated(clean_text, mapped_code):
                # Try to detect the actual language from transliterated text
                corrected_lang = self._detect_language_from_transliterated(clean_text)
                if corrected_lang:
                    logger.info(f"✅ Transliterated text detected as {mapped_code}, corrected to {corrected_lang}")
                    return corrected_lang
            
            logger.info(f"googletrans detected '{detected_code}', mapped to '{mapped_code}'")
            
            if detected_code != mapped_code:
                logger.info(f"✅ Language code mapped: {detected_code} → {mapped_code}")
            else:
                logger.info(f"ℹ️  No mapping needed for: {detected_code}")
            
            return mapped_code
        except (OSError, ImportError, AttributeError, ValueError, requests.RequestException) as e:
            logger.error(f"Language detection failed: {e}")
            return 'unknown'
    
    def _is_likely_transliterated(self, text: str, detected_language: str) -> bool:
        """Check if text is likely transliterated from voice transcription"""
        # Languages that should have non-Latin scripts
        non_latin_scripts = {
            'he', 'ar', 'ru', 'zh', 'ja', 'ko', 'th', 'hi', 'bn', 'ta', 'te', 
            'gu', 'kn', 'ml', 'si', 'fa', 'ur', 'el', 'bg', 'uk', 'sr', 'mk', 
            'mn', 'ka', 'hy', 'am', 'ne'
        }
        
        if detected_language not in non_latin_scripts:
            return False  # Language uses Latin script, so no transliteration issue
        
        # Check if text contains mostly Latin characters when it should contain non-Latin
        latin_chars = sum(1 for c in text if c.isalpha() and ord(c) < 128)
        total_alpha_chars = sum(1 for c in text if c.isalpha())
        
        if total_alpha_chars == 0:
            return False
        
        latin_ratio = latin_chars / total_alpha_chars
        logger.info(f"Transliteration analysis for {detected_language}: {latin_chars}/{total_alpha_chars} chars ({latin_ratio:.2%} Latin)")
        
        # If more than 80% are Latin characters, it's likely transliterated
        return latin_ratio > 0.8
    
    def _detect_language_from_transliterated(self, text: str) -> Optional[str]:
        """Detect language from transliterated text using common patterns"""
        text_lower = text.lower()
        
        # Common transliteration patterns for different languages
        language_patterns = {
            'he': ['shalom', 'mashlomha', 'toda', 'bevakasha', 'ken', 'lo', 'ani', 'ata', 'at'],
            'ru': ['privet', 'kak dela', 'horosho', 'plokho', 'da', 'net', 'spasibo', 'pozhaluysta'],
            'ar': ['marhaba', 'ahlan', 'shukran', 'afwan', 'naam', 'la', 'ana', 'anta', 'anti'],
            'hi': ['namaste', 'dhanyavad', 'kripya', 'haan', 'nahi', 'main', 'aap', 'tum'],
            'th': ['sawadee', 'khob khun', 'khop khun', 'chai', 'mai', 'chan', 'khun', 'phom'],
            'el': ['yassou', 'efcharisto', 'parakalo', 'ne', 'oxi', 'ego', 'esi', 'esu'],
            'fa': ['salam', 'merci', 'lotfan', 'bale', 'na', 'man', 'to', 'shoma'],
            'ur': ['assalam', 'shukriya', 'mehrbani', 'haan', 'nahi', 'main', 'aap', 'tum']
        }
        
        # Count matches for each language
        language_scores = {}
        for lang, patterns in language_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in text_lower:
                    score += 1
            if score > 0:
                language_scores[lang] = score
        
        # Return the language with the highest score if significant
        if language_scores:
            best_lang = max(language_scores, key=language_scores.get)
            best_score = language_scores[best_lang]
            
            # Require at least 2 pattern matches to be confident
            if best_score >= 2:
                logger.info(f"Detected {best_lang} from transliterated patterns (score: {best_score})")
                return best_lang
        
        return None
    
    def _contains_hebrew_characters(self, text: str) -> bool:
        """Check if text contains Hebrew characters"""
        # Hebrew Unicode range: U+0590 to U+05FF
        hebrew_range = range(0x0590, 0x0600)
        
        for char in text:
            if ord(char) in hebrew_range:
                return True
        return False 