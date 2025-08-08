import logging
import asyncio
import requests
from typing import Optional, Dict, Tuple
import unicodedata

logger = logging.getLogger(__name__)

class FreeTranslator:
    """Free translation using Google Translate"""
    
    def __init__(self):
        # Language script detection ranges
        self.script_ranges = {
            'he': range(0x0590, 0x0600),  # Hebrew
            'ar': range(0x0600, 0x0700),  # Arabic
            'th': range(0x0E00, 0x0E80),  # Thai
            'hi': range(0x0900, 0x0980),  # Devanagari (Hindi)
            'bn': range(0x0980, 0x0A00),  # Bengali
            'ta': range(0x0B80, 0x0C00),  # Tamil
            'te': range(0x0C00, 0x0C80),  # Telugu
            'kn': range(0x0C80, 0x0D00),  # Kannada
            'ml': range(0x0D00, 0x0D80),  # Malayalam
            'gu': range(0x0A80, 0x0B00),  # Gujarati
            'pa': range(0x0A00, 0x0A80),  # Gurmukhi (Punjabi)
            'or': range(0x0B00, 0x0B80),  # Odia
            'si': range(0x0D80, 0x0E00),  # Sinhala
            'my': range(0x1000, 0x1100),  # Myanmar
            'ka': range(0x10A0, 0x1100),  # Georgian
            'am': range(0x1200, 0x1380),  # Ethiopic
            'ko': range(0xAC00, 0xD7AF),  # Hangul (Korean)
            'ja': range(0x3040, 0x3100),  # Hiragana
            'zh': range(0x4E00, 0x9FFF),  # CJK Unified Ideographs
        }
        
        # Language code mapping for googletrans inconsistencies
        self.language_mapping = {
            'iw': 'he',  # googletrans returns 'iw' for Hebrew
            'zh-cn': 'zh',  # Simplified Chinese
            'zh-tw': 'zh',  # Traditional Chinese
            'zh-hk': 'zh',  # Hong Kong Chinese
            'zh-sg': 'zh',  # Singapore Chinese
        }
    
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
        """Detect language of text using multiple methods for accuracy"""
        try:
            from googletrans import Translator
            translator = Translator()
            
            # Clean the text first
            clean_text = ' '.join(text.split())
            
            # Method 1: Google Translate detection
            detection = asyncio.run(translator.detect(clean_text))
            detected_code = detection.lang
            confidence = getattr(detection, 'confidence', 0.0)
            
            # Method 2: Unicode script analysis
            script_detection = self._detect_script_by_unicode(clean_text)
            
            # Method 3: Cross-validate and resolve conflicts
            final_code = self._resolve_language_detection(
                detected_code, confidence, script_detection, clean_text
            )
            
            logger.info(f"Language detection: Google='{detected_code}' (conf={confidence:.2f}), "
                       f"Script='{script_detection}', Final='{final_code}'")
            
            return final_code
            
        except (OSError, ImportError, AttributeError, ValueError, requests.RequestException) as e:
            logger.error(f"Language detection failed: {e}")
            return 'unknown'
    
    def _detect_script_by_unicode(self, text: str) -> Optional[str]:
        """Detect script/language using Unicode character ranges"""
        if not text:
            return None
        
        script_counts = {}
        total_chars = 0
        
        for char in text:
            if char.isspace() or unicodedata.category(char).startswith('P'):
                continue  # Skip whitespace and punctuation
                
            char_code = ord(char)
            total_chars += 1
            
            for lang_code, unicode_range in self.script_ranges.items():
                if char_code in unicode_range:
                    script_counts[lang_code] = script_counts.get(lang_code, 0) + 1
                    break
        
        if not script_counts or total_chars == 0:
            return None
        
        # Find the script with the highest percentage
        best_script = max(script_counts.items(), key=lambda x: x[1])
        script_percentage = best_script[1] / total_chars
        
        # Only return if we have a significant percentage of characters in this script
        if script_percentage >= 0.3:  # At least 30% of characters
            logger.info(f"Unicode script detection: {best_script[0]} ({script_percentage:.2%})")
            return best_script[0]
        
        return None
    
    def _resolve_language_detection(self, google_code: str, confidence: float, 
                                  script_code: Optional[str], text: str) -> str:
        """Resolve conflicts between different detection methods"""
        
        # Apply language code mapping
        mapped_code = self.language_mapping.get(google_code, google_code)
        
        # If confidence is high and no script conflict, trust Google
        if confidence > 0.8 and (script_code is None or script_code == mapped_code):
            return mapped_code
        
        # If script detection found something and Google confidence is low, trust script
        if script_code and confidence < 0.6:
            logger.info(f"Low confidence Google detection ({confidence:.2f}), "
                       f"trusting script detection: {script_code}")
            return script_code
        
        # If there's a conflict between Google and script detection
        if script_code and script_code != mapped_code:
            # Use script detection for specific scripts that Google often misidentifies
            if script_code in ['he', 'ar', 'th', 'ko', 'ja', 'zh']:
                logger.info(f"Google misidentified {script_code} as {mapped_code}, "
                           f"correcting to {script_code}")
                return script_code
        
        return mapped_code 