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
        # user_preferences now stores language pairs: {user_id: (lang1, lang2)} or {chat_id: (lang1, lang2)}
        self.user_preferences = {}
        self.user_stats = {}
        
        # State management for two-step language selection
        # {user_id: {'step': 'first_lang' or 'second_lang', 'first_lang': 'lang_code'}}
        self.language_selection_state = {}
        
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
            
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to send keyboard: {e}")
            return False
    
    def get_user_language_pair(self, user_id: int, chat_id: int = None) -> Tuple[str, str]:
        """Get user's language pair (supports both user and group chat preferences)"""
        # For group chats, use chat_id; for private chats, use user_id
        key = chat_id if chat_id and chat_id < 0 else user_id
        return self.user_preferences.get(key, ('en', 'ru'))
    
    def set_user_language_pair(self, user_id: int, lang1: str, lang2: str, chat_id: int = None) -> bool:
        """Set user's language pair (supports both user and group chat preferences)"""
        if (LanguageDetector.is_valid_language(lang1) and 
            LanguageDetector.is_valid_language(lang2) and 
            lang1 != lang2):
            # For group chats, use chat_id; for private chats, use user_id
            key = chat_id if chat_id and chat_id < 0 else user_id
            self.user_preferences[key] = (lang1.lower(), lang2.lower())
            return True
        return False
    
    def update_user_stats(self, user_id: int):
        """Update user translation statistics"""
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {'translations': 0, 'joined': datetime.now()}
        self.user_stats[user_id]['translations'] += 1
    
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
        lang1, lang2 = self.get_user_language_pair(user_id, chat_id)
        detected_lang = self.translator.detect_language(text)
        
        # Determine target language based on detected language and language pair
        if detected_lang == lang1:
            target_lang = lang2
        elif detected_lang == lang2:
            target_lang = lang1
        else:
            # If detected language is neither of the pair, translate to lang2 (second language in pair)
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
        
        # Handle two-step language selection
        if user_id in self.language_selection_state:
            self._handle_language_selection(chat_id, user_id, data)
        # Handle legacy language pair selection (for backward compatibility)
        elif '|' in data:  # Format: "flag1|flag2"
            self._handle_legacy_language_selection(chat_id, user_id, data)
    
    def _handle_language_selection(self, chat_id: int, user_id: int, data: str) -> None:
        """Handle two-step language selection process"""
        state = self.language_selection_state[user_id]
        selected_lang_code = self._extract_language_code(data)
        
        if not selected_lang_code:
            self.send_message(chat_id, "❌ Invalid language selection. Please try again.")
            return
        
        if state['step'] == 'first_lang':
            self._handle_first_language_selection(chat_id, user_id, selected_lang_code)
        elif state['step'] == 'second_lang':
            self._handle_second_language_selection(chat_id, user_id, selected_lang_code)
    
    def _extract_language_code(self, data: str) -> str | None:
        """Extract language code from callback data"""
        if data in LanguageDetector.SUPPORTED_LANGUAGES:
            return data
        return self._get_language_code_from_button(data)
    
    def _handle_first_language_selection(self, chat_id: int, user_id: int, selected_lang_code: str) -> None:
        """Handle first language selection in two-step process"""
        state = self.language_selection_state[user_id]
        state['step'] = 'second_lang'
        state['first_lang'] = selected_lang_code
        
        first_lang_name = LanguageDetector.SUPPORTED_LANGUAGES[selected_lang_code]
        first_flag = self._get_language_flag(selected_lang_code)
        
        keyboard = self._create_language_keyboard(exclude_lang=selected_lang_code)
        text = f"✅ *First language selected: {first_flag} {first_lang_name}*\n\nNow choose your second language:"
        self.send_keyboard(chat_id, text, keyboard)
    
    def _handle_second_language_selection(self, chat_id: int, user_id: int, selected_lang_code: str) -> None:
        """Handle second language selection in two-step process"""
        state = self.language_selection_state[user_id]
        first_lang = state['first_lang']
        second_lang = selected_lang_code
        
        if self.set_user_language_pair(user_id, first_lang, second_lang, chat_id):
            self._send_language_pair_confirmation(chat_id, first_lang, second_lang)
        else:
            self.send_message(chat_id, "❌ Failed to set language pair. Please try again.")
        
        del self.language_selection_state[user_id]
    
    def _send_language_pair_confirmation(self, chat_id: int, first_lang: str, second_lang: str) -> None:
        """Send confirmation message for language pair setup"""
        first_lang_name = LanguageDetector.SUPPORTED_LANGUAGES[first_lang]
        second_lang_name = LanguageDetector.SUPPORTED_LANGUAGES[second_lang]
        first_flag = self._get_language_flag(first_lang)
        second_flag = self._get_language_flag(second_lang)
        
        response = f"✅ *Language pair set to {first_flag} {first_lang_name} ↔ {second_flag} {second_lang_name}*\n\nNow send me any message and I'll translate between these languages!"
        self.send_message(chat_id, response)
    
    def _handle_legacy_language_selection(self, chat_id: int, user_id: int, data: str) -> None:
        """Handle legacy language pair selection format"""
        flag1, flag2 = data.split('|')
        lang1 = self._get_language_from_flag(flag1)
        lang2 = self._get_language_from_flag(flag2)
        
        if lang1 and lang2 and self.set_user_language_pair(user_id, lang1, lang2, chat_id):
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
            # Start two-step language selection process
            self.language_selection_state[user_id] = {'step': 'first_lang'}
            
            # Create keyboard with all available languages
            keyboard = self._create_language_keyboard()
            
            text = "🌍 *Step 1: Choose your first language*\n\nSelect the first language for your translation pair:"
            self.send_keyboard(chat_id, text, keyboard)
            
        elif cmd == '/languages':
            lang_list = LanguageDetector.get_language_list()
            response = f"🌍 *Supported Languages:*\n\n```\n{lang_list}\n```\n\nUse `/setpair` to choose your language pair!"
            self.send_message(chat_id, response)
            
        elif cmd == '/stats':
            stats = self.user_stats.get(user_id, {'translations': 0})
            current_pair = self.get_user_language_pair(user_id, chat_id)
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