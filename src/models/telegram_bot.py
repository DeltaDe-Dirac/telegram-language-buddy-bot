import os
import requests
import logging
from typing import Dict, List, Tuple
from datetime import datetime

from .language_detector import LanguageDetector
from .free_translator import FreeTranslator

logger = logging.getLogger(__name__)

class TelegramBot:
    """Telegram Bot API integration"""
    
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.translator = FreeTranslator()
        
        # In-memory storage (use database in production)
        # user_preferences now stores language pairs: {user_id: (lang1, lang2)}
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
    
    def get_user_language_pair(self, user_id: int) -> Tuple[str, str]:
        """Get user's language pair"""
        return self.user_preferences.get(user_id, ('en', 'ru'))
    
    def set_user_language_pair(self, user_id: int, lang1: str, lang2: str) -> bool:
        """Set user's language pair"""
        if (LanguageDetector.is_valid_language(lang1) and 
            LanguageDetector.is_valid_language(lang2) and 
            lang1 != lang2):
            self.user_preferences[user_id] = (lang1.lower(), lang2.lower())
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
        lang1, lang2 = self.get_user_language_pair(user_id)
        detected_lang = self.translator.detect_language(text)
        
        # Determine target language based on detected language
        if detected_lang == lang1:
            target_lang = lang2
        elif detected_lang == lang2:
            target_lang = lang1
        else:
            # If detected language is neither of the pair, translate to lang2
            target_lang = lang2
        
        # Don't translate if already in target language
        if detected_lang == target_lang:
            response = f"✅ *Already in {LanguageDetector.SUPPORTED_LANGUAGES.get(target_lang, target_lang)}*\n\n_{text}_"
            self.send_message(chat_id, response)
            return
        
        # Translate the message
        translated = self.translator.translate_text(text, target_lang, detected_lang)
        
        if translated and translated != text:
            self.update_user_stats(user_id)
            
            response = f"🔤 *Translation* ({detected_lang} → {target_lang})\n\n"
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
        
        # Handle language pair selection
        if '|' in data:  # Format: "lang1|lang2"
            lang1, lang2 = data.split('|')
            if self.set_user_language_pair(user_id, lang1, lang2):
                lang1_name = LanguageDetector.SUPPORTED_LANGUAGES[lang1]
                lang2_name = LanguageDetector.SUPPORTED_LANGUAGES[lang2]
                response = f"✅ *Language pair set to {lang1_name} ↔ {lang2_name}*\n\nNow send me any message and I'll translate between these languages!"
                self.send_message(chat_id, response)
    
    def _handle_command(self, chat_id: int, user_id: int, command: str) -> None:
        """Handle bot commands"""
        cmd_parts = command.split()
        cmd = cmd_parts[0].lower()
        
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

_Need help? Just ask!_ 💬
            """
            self.send_message(chat_id, help_text)
            
        elif cmd == '/setpair':
            # Show popular language pairs
            popular_pairs = [
                ['🇹🇭 Thai ↔ 🇷🇺 Russian', '🇨🇳 Chinese ↔ 🇺🇸 English'],
                ['🇪🇸 Spanish ↔ 🇫🇷 French', '🇩🇪 German ↔ 🇮🇹 Italian'],
                ['🇯🇵 Japanese ↔ 🇰🇷 Korean', '🇸🇦 Arabic ↔ 🇮🇳 Hindi'],
                ['🇵🇱 Polish ↔ 🇨🇿 Czech', '🇳🇱 Dutch ↔ 🇸🇪 Swedish']
            ]
            
            # Map display names to language codes
            pair_map = {
                '🇹🇭 Thai ↔ 🇷🇺 Russian': 'th|ru',
                '🇨🇳 Chinese ↔ 🇺🇸 English': 'zh|en',
                '🇪🇸 Spanish ↔ 🇫🇷 French': 'es|fr',
                '🇩🇪 German ↔ 🇮🇹 Italian': 'de|it',
                '🇯🇵 Japanese ↔ 🇰🇷 Korean': 'ja|ko',
                '🇸🇦 Arabic ↔ 🇮🇳 Hindi': 'ar|hi',
                '🇵🇱 Polish ↔ 🇨🇿 Czech': 'pl|cs',
                '🇳🇱 Dutch ↔ 🇸🇪 Swedish': 'nl|sv'
            }
            
            # Convert to callback data
            keyboard = []
            for row in popular_pairs:
                keyboard_row = []
                for pair_display in row:
                    keyboard_row.append(pair_map.get(pair_display, pair_display))
                keyboard.append(keyboard_row)
            
            text = "🌍 *Choose your language pair:*\n\nClick on your preferred language pair below:"
            self.send_keyboard(chat_id, text, keyboard)
            
        elif cmd == '/languages':
            lang_list = LanguageDetector.get_language_list()
            response = f"🌍 *Supported Languages:*\n\n```\n{lang_list}\n```\n\nUse `/setpair` to choose your language pair!"
            self.send_message(chat_id, response)
            
        elif cmd == '/stats':
            stats = self.user_stats.get(user_id, {'translations': 0})
            current_pair = self.get_user_language_pair(user_id)
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