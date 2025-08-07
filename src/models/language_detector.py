class LanguageDetector:
    """Language detection and management"""
    
    SUPPORTED_LANGUAGES = {
        'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
        'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'zh': 'Chinese',
        'ja': 'Japanese', 'ko': 'Korean', 'ar': 'Arabic', 'hi': 'Hindi',
        'tr': 'Turkish', 'pl': 'Polish', 'nl': 'Dutch', 'sv': 'Swedish',
        'da': 'Danish', 'no': 'Norwegian', 'fi': 'Finnish', 'el': 'Greek',
        'he': 'Hebrew', 'th': 'Thai', 'vi': 'Vietnamese', 'id': 'Indonesian',
        'ms': 'Malay', 'tl': 'Filipino', 'uk': 'Ukrainian', 'cs': 'Czech',
        'sk': 'Slovak', 'hu': 'Hungarian', 'ro': 'Romanian', 'bg': 'Bulgarian',
        'hr': 'Croatian', 'sr': 'Serbian', 'sl': 'Slovenian', 'et': 'Estonian',
        'lv': 'Latvian', 'lt': 'Lithuanian', 'fa': 'Persian', 'ur': 'Urdu',
        'bn': 'Bengali', 'ta': 'Tamil', 'te': 'Telugu', 'mr': 'Marathi',
        'gu': 'Gujarati', 'kn': 'Kannada', 'ml': 'Malayalam', 'si': 'Sinhala'
    }
    
    @classmethod
    def get_language_list(cls) -> str:
        """Get formatted list of supported languages"""
        langs = []
        for code, name in sorted(cls.SUPPORTED_LANGUAGES.items()):
            langs.append(f"`{code}` - {name}")
        return "\n".join(langs)
    
    @classmethod
    def is_valid_language(cls, lang_code: str) -> bool:
        """Check if language code is supported"""
        if not lang_code or not isinstance(lang_code, str):
            return False
        return lang_code.strip().lower() in cls.SUPPORTED_LANGUAGES 