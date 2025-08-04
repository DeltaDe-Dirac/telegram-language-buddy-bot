import os
import json
import requests
from flask import Flask, request, jsonify
import logging
from typing import Dict, Optional, List
import re
from datetime import datetime
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

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
        return lang_code.lower() in cls.SUPPORTED_LANGUAGES

class FreeTranslator:
    """Free translation using multiple services"""
    
    def __init__(self):
        self.hf_token = os.getenv('HUGGINGFACE_API_TOKEN')
        self.hf_base_url = "https://api-inference.huggingface.co/models"
        
        # Model priority (best to fallback)
        self.models = [
            "facebook/nllb-200-distilled-600M",     # Best quality, 200 languages
            "facebook/mbart-large-50-many-to-many-mmt",  # Good quality, 50 languages
            "Helsinki-NLP/opus-mt-mul-en",          # Lightweight, to English only
        ]
        
    def translate_text(self, text: str, target_lang: str, source_lang: str = 'auto') -> Optional[str]:
        """Translate text using available free services"""
        
        # Try Hugging Face models first if token is available
        if self.hf_token:
            for model in self.models:
                result = self._translate_huggingface(text, target_lang, source_lang, model)
                if result:
                    return result
                    
        # Fallback to Google Translate
        return self._translate_googletrans(text, target_lang, source_lang)
    
    def _translate_huggingface(self, text: str, target_lang: str, source_lang: str, model: str) -> Optional[str]:
        """Translate using Hugging Face Inference API with specified model"""
        try:
            headers = {"Authorization": f"Bearer {self.hf_token}"}
            
            if "nllb" in model.lower():
                return self._translate_nllb(text, target_lang, source_lang, model, headers)
            elif "mbart" in model.lower():
                return self._translate_mbart(text, target_lang, source_lang, model, headers)
            else:  # OPUS-MT models
                return self._translate_opus(text, target_lang, source_lang, model, headers)
                
        except Exception as e:
            logger.warning(f"Hugging Face translation failed with {model}: {e}")
            
        return None
    
    def _translate_nllb(self, text: str, target_lang: str, source_lang: str, model: str, headers: dict) -> Optional[str]:
        """Translate using NLLB-200 model"""
        try:
            headers = {"Authorization": f"Bearer {self.hf_token}"}
            
            # Use NLLB-200 model (best multilingual translator)
            model = "facebook/nllb-200-distilled-600M"
            
            # NLLB language code mapping
            lang_mapping = {
                'en': 'eng_Latn', 'es': 'spa_Latn', 'fr': 'fra_Latn', 'de': 'deu_Latn',
                'it': 'ita_Latn', 'pt': 'por_Latn', 'ru': 'rus_Cyrl', 'zh': 'zho_Hans',
                'ja': 'jpn_Jpan', 'ko': 'kor_Hang', 'ar': 'arb_Arab', 'hi': 'hin_Deva',
                'tr': 'tur_Latn', 'pl': 'pol_Latn', 'nl': 'nld_Latn', 'sv': 'swe_Latn',
                'da': 'dan_Latn', 'no': 'nor_Latn', 'fi': 'fin_Latn', 'el': 'ell_Grek',
                'he': 'heb_Hebr', 'th': 'tha_Thai', 'vi': 'vie_Latn', 'id': 'ind_Latn',
                'ms': 'zsm_Latn', 'tl': 'tgl_Latn', 'uk': 'ukr_Cyrl', 'cs': 'ces_Latn',
                'sk': 'slk_Latn', 'hu': 'hun_Latn', 'ro': 'ron_Latn', 'bg': 'bul_Cyrl',
                'hr': 'hrv_Latn', 'sr': 'srp_Cyrl', 'sl': 'slv_Latn', 'et': 'est_Latn',
                'lv': 'lav_Latn', 'lt': 'lit_Latn', 'fa': 'pes_Arab', 'ur': 'urd_Arab',
                'bn': 'ben_Beng', 'ta': 'tam_Taml', 'te': 'tel_Telu', 'mr': 'mar_Deva',
                'gu': 'guj_Gujr', 'kn': 'kan_Knda', 'ml': 'mal_Mlym', 'si': 'sin_Sinh'
            }
            
            # Get NLLB language codes
            src_lang_code = lang_mapping.get(source_lang, 'eng_Latn')
            tgt_lang_code = lang_mapping.get(target_lang, 'eng_Latn')
            
            # Auto-detect source language if needed
            if source_lang == 'auto':
                detected = self.detect_language(text)
                src_lang_code = lang_mapping.get(detected, 'eng_Latn')
            
            payload = {
                "inputs": text,
                "parameters": {
                    "src_lang": src_lang_code,
                    "tgt_lang": tgt_lang_code
                }
            }
            
            response = requests.post(
                f"{self.hf_base_url}/{model}",
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('translation_text')
                elif isinstance(result, dict):
                    return result.get('translation_text')
                    
        except Exception as e:
            logger.warning(f"NLLB-200 translation failed: {e}")
            
        return None
    
    def _translate_mbart(self, text: str, target_lang: str, source_lang: str, model: str, headers: dict) -> Optional[str]:
        """Translate using mBART model"""
        try:
            # mBART language code mapping
            lang_mapping = {
                'en': 'en_XX', 'es': 'es_XX', 'fr': 'fr_XX', 'de': 'de_DE',
                'it': 'it_IT', 'pt': 'pt_XX', 'ru': 'ru_RU', 'zh': 'zh_CN',
                'ja': 'ja_XX', 'ko': 'ko_KR', 'ar': 'ar_AR', 'hi': 'hi_IN',
                'tr': 'tr_TR', 'pl': 'pl_PL', 'nl': 'nl_XX', 'sv': 'sv_SE',
                'da': 'da_DK', 'no': 'no_NO', 'fi': 'fi_FI', 'el': 'el_GR',
                'he': 'he_IL', 'th': 'th_TH', 'vi': 'vi_VN', 'id': 'id_ID',
                'ms': 'ms_MY', 'tl': 'tl_XX', 'uk': 'uk_UA', 'cs': 'cs_CZ',
                'sk': 'sk_SK', 'hu': 'hu_HU', 'ro': 'ro_RO', 'bg': 'bg_BG',
                'hr': 'hr_HR', 'sr': 'sr_RS', 'sl': 'sl_SI', 'et': 'et_EE',
                'lv': 'lv_LV', 'lt': 'lt_LT', 'fa': 'fa_IR', 'ur': 'ur_PK',
                'bn': 'bn_IN', 'ta': 'ta_IN', 'te': 'te_IN', 'mr': 'mr_IN',
                'gu': 'gu_IN', 'kn': 'kn_IN', 'ml': 'ml_IN', 'si': 'si_LK'
            }
            
            # Get mBART language codes
            src_lang_code = lang_mapping.get(source_lang, 'en_XX')
            tgt_lang_code = lang_mapping.get(target_lang, 'en_XX')
            
            # Auto-detect source language if needed
            if source_lang == 'auto':
                detected = self.detect_language(text)
                src_lang_code = lang_mapping.get(detected, 'en_XX')
            
            payload = {
                "inputs": text,
                "parameters": {
                    "src_lang": src_lang_code,
                    "tgt_lang": tgt_lang_code
                }
            }
            
            response = requests.post(
                f"{self.hf_base_url}/{model}",
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('translation_text')
                elif isinstance(result, dict):
                    return result.get('translation_text')
                    
        except Exception as e:
            logger.warning(f"mBART translation failed: {e}")
            
        return None
    
    def _translate_opus(self, text: str, target_lang: str, source_lang: str, model: str, headers: dict) -> Optional[str]:
        """Translate using OPUS-MT models"""
        try:
            payload = {"inputs": text}
            
            response = requests.post(
                f"{self.hf_base_url}/{model}",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('translation_text')
                    
        except Exception as e:
            logger.warning(f"OPUS-MT translation failed: {e}")
            
        return None
    
    def _translate_googletrans(self, text: str, target_lang: str, source_lang: str) -> str:
        """Translate using Google Translate (free library)"""
        try:
            from googletrans import Translator
            translator = Translator()
            
            if source_lang == 'auto':
                result = translator.translate(text, dest=target_lang)
            else:
                result = translator.translate(text, src=source_lang, dest=target_lang)
            
            return result.text
            
        except Exception as e:
            logger.error(f"Google Translate failed: {e}")
            return f"❌ Translation failed: {str(e)}"
    
    def detect_language(self, text: str) -> str:
        """Detect language of text"""
        try:
            from googletrans import Translator
            translator = Translator()
            detection = translator.detect(text)
            return detection.lang
        except:
            return 'unknown'

class TelegramBot:
    """Telegram Bot API integration"""
    
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.translator = FreeTranslator()
        
        # In-memory storage (use database in production)
        self.user_preferences = {}
        self.user_stats = {}
        
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    
    def send_message(self, chat_id: int, text: str, parse_mode: str = 'Markdown') -> bool:
        """Send message to Telegram chat"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def send_keyboard(self, chat_id: int, text: str, keyboard: List[List[str]]) -> bool:
        """Send message with inline keyboard"""
        try:
            url = f"{self.base_url}/sendMessage"
            
            # Create inline keyboard
            inline_keyboard = []
            for row in keyboard:
                inline_row = []
                for button in row:
                    inline_row.append({
                        'text': button,
                        'callback_data': button.lower()
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
            
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to send keyboard: {e}")
            return False
    
    def get_user_language(self, user_id: int) -> str:
        """Get user's preferred language"""
        return self.user_preferences.get(user_id, 'en')
    
    def set_user_language(self, user_id: int, lang_code: str) -> bool:
        """Set user's preferred language"""
        if LanguageDetector.is_valid_language(lang_code):
            self.user_preferences[user_id] = lang_code.lower()
            return True
        return False
    
    def update_user_stats(self, user_id: int):
        """Update user translation statistics"""
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {'translations': 0, 'joined': datetime.now()}
        self.user_stats[user_id]['translations'] += 1
    
    def process_message(self, update: Dict) -> None:
        """Process incoming Telegram message"""
        try:
            if 'message' in update:
                self._handle_message(update['message'])
            elif 'callback_query' in update:
                self._handle_callback_query(update['callback_query'])
                
        except Exception as e:
            logger.error(f"Error processing update: {e}")
    
    def _handle_message(self, message: Dict) -> None:
        """Handle regular text message"""
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        text = message.get('text', '').strip()
        
        if not text:
            return
        
        # Handle commands
        if text.startswith('/'):
            self._handle_command(chat_id, user_id, text)
            return
        
        # Regular message - translate it
        user_lang = self.get_user_language(user_id)
        detected_lang = self.translator.detect_language(text)
        
        # Don't translate if already in target language
        if detected_lang == user_lang:
            response = f"✅ *Already in {LanguageDetector.SUPPORTED_LANGUAGES.get(user_lang, user_lang)}*\n\n_{text}_"
            self.send_message(chat_id, response)
            return
        
        # Translate the message
        translated = self.translator.translate_text(text, user_lang, detected_lang)
        
        if translated and translated != text:
            self.update_user_stats(user_id)
            
            response = f"🔤 *Translation* ({detected_lang} → {user_lang})\n\n"
            response += f"*Original:* {text}\n\n"
            response += f"*Translation:* {translated}"
            
            self.send_message(chat_id, response)
        else:
            self.send_message(chat_id, "❌ Translation failed. Please try again.")
    
    def _handle_callback_query(self, callback_query: Dict) -> None:
        """Handle inline keyboard callback"""
        chat_id = callback_query['message']['chat']['id']
        user_id = callback_query['from']['id']
        data = callback_query['data']
        
        # Handle language selection
        if LanguageDetector.is_valid_language(data):
            if self.set_user_language(user_id, data):
                lang_name = LanguageDetector.SUPPORTED_LANGUAGES[data]
                response = f"✅ *Language set to {lang_name}*\n\nNow send me any message and I'll translate it to {lang_name}!"
                self.send_message(chat_id, response)
    
    def _handle_command(self, chat_id: int, user_id: int, command: str) -> None:
        """Handle bot commands"""
        cmd_parts = command.split()
        cmd = cmd_parts[0].lower()
        
        if cmd == '/start':
            welcome_text = """
🤖 *Welcome to Language Buddy Bot!*

I can translate any message to your preferred language instantly!

*Commands:*
/setlang - Choose your preferred language
/stats - View your translation statistics
/help - Show help information
/languages - List all supported languages

*Quick Start:*
1. Use /setlang to choose your language
2. Send me any text message
3. Get instant translation!

_Just send me a message to get started!_ 🚀
            """
            self.send_message(chat_id, welcome_text)
            
        elif cmd == '/help':
            help_text = """
🆘 *Language Buddy Bot Help*

*How it works:*
• Send any text message and I'll translate it to your preferred language
• I auto-detect the source language
• Translations are powered by AI models

*Commands:*
• `/start` - Welcome message
• `/setlang` - Choose your preferred language
• `/stats` - View your translation statistics
• `/languages` - List all supported languages
• `/help` - Show this help

*Pro Tips:*
• Set your language once with /setlang
• I support 40+ languages
• Works with any text length
• Free and unlimited!

_Need help? Just ask!_ 💬
            """
            self.send_message(chat_id, help_text)
            
        elif cmd == '/setlang':
            # Show popular languages first
            popular_langs = [
                ['🇺🇸 English', '🇪🇸 Spanish', '🇫🇷 French'],
                ['🇩🇪 German', '🇮🇹 Italian', '🇵🇹 Portuguese'],
                ['🇷🇺 Russian', '🇨🇳 Chinese', '🇯🇵 Japanese'],
                ['🇰🇷 Korean', '🇸🇦 Arabic', '🇮🇳 Hindi']
            ]
            
            # Map display names to language codes
            lang_map = {
                '🇺🇸 English': 'en', '🇪🇸 Spanish': 'es', '🇫🇷 French': 'fr',
                '🇩🇪 German': 'de', '🇮🇹 Italian': 'it', '🇵🇹 Portuguese': 'pt',
                '🇷🇺 Russian': 'ru', '🇨🇳 Chinese': 'zh', '🇯🇵 Japanese': 'ja',
                '🇰🇷 Korean': 'ko', '🇸🇦 Arabic': 'ar', '🇮🇳 Hindi': 'hi'
            }
            
            # Convert to callback data
            keyboard = []
            for row in popular_langs:
                keyboard_row = []
                for lang_display in row:
                    keyboard_row.append(lang_map.get(lang_display, lang_display))
                keyboard.append(keyboard_row)
            
            text = "🌍 *Choose your preferred language:*\n\nClick on your language below:"
            self.send_keyboard(chat_id, text, keyboard)
            
        elif cmd == '/languages':
            lang_list = LanguageDetector.get_language_list()
            response = f"🌍 *Supported Languages:*\n\n```\n{lang_list}\n```\n\nUse `/setlang` to choose your language!"
            self.send_message(chat_id, response)
            
        elif cmd == '/stats':
            stats = self.user_stats.get(user_id, {'translations': 0})
            current_lang = self.get_user_language(user_id)
            lang_name = LanguageDetector.SUPPORTED_LANGUAGES.get(current_lang, current_lang)
            
            response = f"""
📊 *Your Translation Stats:*

🔤 **Translations:** {stats['translations']}
🌍 **Current Language:** {lang_name} (`{current_lang}`)
📅 **Member Since:** {stats.get('joined', 'Unknown')}

_Keep translating to increase your stats!_ 🚀
            """
            self.send_message(chat_id, response)
            
        else:
            self.send_message(chat_id, "❓ Unknown command. Use /help to see available commands.")

# Initialize the bot (will be created when needed)
bot = None

def get_bot():
    """Get or create bot instance"""
    global bot
    if bot is None:
        bot = TelegramBot()
    return bot

@app.route('/')
def home():
    """Health check endpoint"""
    return {
        "status": "active",
        "service": "Telegram Language Buddy Bot",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Telegram webhook"""
    try:
        update = request.get_json()
        logger.info(f"Received update: {json.dumps(update, indent=2)}")
        
        get_bot().process_message(update)
        return jsonify({"ok": True})
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/set_webhook', methods=['POST'])
def set_webhook():
    """Set Telegram webhook URL"""
    try:
        webhook_url = request.json.get('url')
        if not webhook_url:
            return jsonify({"error": "URL is required"}), 400
        
        url = f"{get_bot().base_url}/setWebhook"
        payload = {"url": webhook_url}
        
        response = requests.post(url, json=payload)
        result = response.json()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/translate', methods=['POST'])
def manual_translate():
    """Manual translation endpoint for testing"""
    try:
        data = request.get_json()
        text = data.get('text')
        target_lang = data.get('target_lang', 'en')
        source_lang = data.get('source_lang', 'auto')
        
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        translated = get_bot().translator.translate_text(text, target_lang, source_lang)
        detected_lang = get_bot().translator.detect_language(text)
        
        return jsonify({
            "original": text,
            "translated": translated,
            "source_language": detected_lang,
            "target_language": target_lang
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats')
def get_stats():
    """Get bot statistics"""
    try:
        total_users = len(get_bot().user_preferences)
        total_translations = sum(stats.get('translations', 0) for stats in get_bot().user_stats.values())
        
        language_distribution = {}
        for lang in get_bot().user_preferences.values():
            language_distribution[lang] = language_distribution.get(lang, 0) + 1
        
        return jsonify({
            "total_users": total_users,
            "total_translations": total_translations,
            "language_distribution": language_distribution,
            "supported_languages": len(LanguageDetector.SUPPORTED_LANGUAGES)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)