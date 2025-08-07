import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
import os
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.models.telegram_bot import TelegramBot


class TestTelegramBot(unittest.TestCase):
    """Test cases for TelegramBot class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock environment variable
        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'}):
            self.bot = TelegramBot()
    
    def test_bot_initialization(self):
        """Test that bot initializes correctly"""
        self.assertEqual(self.bot.token, 'test_token_123')
        self.assertEqual(self.bot.base_url, 'https://api.telegram.org/bottest_token_123')
        self.assertIsNotNone(self.bot.translator)
        self.assertIsNotNone(self.bot.db)
    
    def test_bot_initialization_missing_token(self):
        """Test that bot raises error when token is missing"""
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError):
                TelegramBot()
    
    @patch('requests.post')
    def test_send_message_success(self, mock_post):
        """Test successful message sending"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Test sending message
        result = self.bot.send_message(12345, "Hello world")
        
        # Verify result
        self.assertTrue(result)
        mock_post.assert_called_once()
        
        # Verify call arguments
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['json']['chat_id'], 12345)
        self.assertEqual(call_args[1]['json']['text'], "Hello world")
        self.assertEqual(call_args[1]['json']['parse_mode'], 'Markdown')
    
    @patch('requests.post')
    def test_send_message_failure(self, mock_post):
        """Test message sending failure"""
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        # Test sending message
        result = self.bot.send_message(12345, "Hello world")
        
        # Verify result
        self.assertFalse(result)
    
    @patch('requests.post')
    def test_send_message_exception(self, mock_post):
        """Test message sending with exception"""
        # Mock RequestException (which is caught by the method)
        from requests import RequestException
        mock_post.side_effect = RequestException("Network error")
        
        # Test sending message
        result = self.bot.send_message(12345, "Hello world")
        
        # Verify result
        self.assertFalse(result)
    
    @patch('requests.post')
    def test_delete_message_success(self, mock_post):
        """Test successful message deletion"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response
        
        # Test deleting message
        result = self.bot.delete_message(12345, 67890)
        
        # Verify result
        self.assertTrue(result)
        mock_post.assert_called_once()
        
        # Verify call arguments
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['json']['chat_id'], 12345)
        self.assertEqual(call_args[1]['json']['message_id'], 67890)
    
    @patch('requests.post')
    def test_delete_message_failure(self, mock_post):
        """Test message deletion failure"""
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"ok": False, "error_code": 400}
        mock_post.return_value = mock_response
        
        # Test deleting message
        result = self.bot.delete_message(12345, 67890)
        
        # Verify result
        self.assertFalse(result)
    
    @patch('requests.post')
    def test_send_keyboard_success(self, mock_post):
        """Test successful keyboard sending"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Test keyboard
        keyboard = [["English", "Spanish"], ["French", "German"]]
        result = self.bot.send_keyboard(12345, "Choose language:", keyboard)
        
        # Verify result
        self.assertTrue(result)
        mock_post.assert_called_once()
        
        # Verify call arguments
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['json']['chat_id'], 12345)
        self.assertEqual(call_args[1]['json']['text'], "Choose language:")
        self.assertIn('reply_markup', call_args[1]['json'])
        self.assertIn('inline_keyboard', call_args[1]['json']['reply_markup'])
    
    @patch('requests.post')
    def test_answer_callback_query_success(self, mock_post):
        """Test successful callback query answering"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Test answering callback
        result = self.bot.answer_callback_query("callback_123", "Selected!")
        
        # Verify result
        self.assertTrue(result)
        mock_post.assert_called_once()
        
        # Verify call arguments
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['json']['callback_query_id'], "callback_123")
        self.assertEqual(call_args[1]['json']['text'], "Selected!")
    
    def test_get_language_flag(self):
        """Test language flag mapping"""
        # Test known languages
        self.assertEqual(self.bot._get_language_flag('en'), '🇺🇸')
        self.assertEqual(self.bot._get_language_flag('es'), '🇪🇸')
        self.assertEqual(self.bot._get_language_flag('fr'), '🇫🇷')
        
        # Test unknown language
        self.assertEqual(self.bot._get_language_flag('unknown'), '🌍')
    
    def test_create_language_keyboard(self):
        """Test language keyboard creation"""
        # Test without exclusion
        keyboard = self.bot._create_language_keyboard()
        self.assertIsInstance(keyboard, list)
        self.assertGreater(len(keyboard), 0)
        
        # Verify structure
        for row in keyboard:
            self.assertIsInstance(row, list)
            self.assertLessEqual(len(row), 3)  # Max 3 per row
            for button in row:
                self.assertIsInstance(button, tuple)
                self.assertEqual(len(button), 2)  # (display_text, callback_data)
        
        # Test with exclusion
        keyboard_excluded = self.bot._create_language_keyboard(exclude_lang='en')
        # Verify 'en' is not in any button
        for row in keyboard_excluded:
            for button in row:
                self.assertNotIn('en', button[1])  # callback_data should not contain 'en'
    
    def test_get_language_code_from_button(self):
        """Test extracting language code from button text"""
        # Test valid button text
        button_text = "🇺🇸 English"
        result = self.bot._get_language_code_from_button(button_text)
        self.assertEqual(result, "en")
        
        # Test invalid button text
        invalid_texts = ["", "English", "🇺🇸", "🇺🇸 English Spanish"]
        for text in invalid_texts:
            result = self.bot._get_language_code_from_button(text)
            self.assertIsNone(result)
    
    @patch.object(TelegramBot, 'get_user_language_pair')
    @patch.object(TelegramBot, 'set_user_language_pair')
    def test_set_user_language_pair_valid(self, mock_set, mock_get):
        """Test setting valid language pair"""
        mock_set.return_value = True
        
        result = self.bot.set_user_language_pair(12345, "en", "es")
        
        self.assertTrue(result)
        mock_set.assert_called_once_with(12345, "en", "es")
    
    def test_set_user_language_pair_invalid(self):
        """Test setting invalid language pair"""
        # Same language
        result = self.bot.set_user_language_pair(12345, "en", "en")
        self.assertFalse(result)
        
        # Invalid language codes
        result = self.bot.set_user_language_pair(12345, "invalid", "en")
        self.assertFalse(result)
        
        result = self.bot.set_user_language_pair(12345, "en", "invalid")
        self.assertFalse(result)
    
    def test_get_user_language_pair_with_preferences(self):
        """Test getting user language pair with existing preferences"""
        # Mock the database method directly on the instance
        self.bot.db.get_user_preferences = lambda chat_id: ("en", "es")
        
        result = self.bot.get_user_language_pair(12345)
        
        self.assertEqual(result, ("en", "es"))
    
    def test_get_user_language_pair_default(self):
        """Test getting user language pair with default fallback"""
        # Mock the database method to return None
        self.bot.db.get_user_preferences = lambda chat_id: None
        
        result = self.bot.get_user_language_pair(12345)
        
        self.assertEqual(result, ("en", "ru"))  # Default fallback
    
    def test_process_message_with_message(self):
        """Test processing message with regular message"""
        update = {
            "message": {
                "chat": {"id": 12345},
                "from": {"id": 67890, "first_name": "Test"},
                "text": "Hello"
            }
        }
        
        with patch.object(self.bot, '_handle_message') as mock_handle:
            self.bot.process_message(update)
            mock_handle.assert_called_once_with(update["message"])
    
    def test_process_message_with_callback_query(self):
        """Test processing message with callback query"""
        update = {
            "callback_query": {
                "id": "callback_123",
                "data": "en",
                "message": {"chat": {"id": 12345}}
            }
        }
        
        with patch.object(self.bot, '_handle_callback_query') as mock_handle:
            self.bot.process_message(update)
            mock_handle.assert_called_once_with(update["callback_query"])
    
    def test_process_message_with_edited_message(self):
        """Test processing message with edited message"""
        update = {
            "edited_message": {
                "chat": {"id": 12345},
                "from": {"id": 67890, "first_name": "Test"},
                "text": "Hello"
            }
        }
        
        with patch.object(self.bot, '_handle_edited_message') as mock_handle:
            self.bot.process_message(update)
            mock_handle.assert_called_once_with(update["edited_message"])
    
    def test_process_message_invalid_update(self):
        """Test processing message with invalid update"""
        invalid_updates = [
            {},
            {"invalid_key": "value"},
            None
        ]
        
        for update in invalid_updates:
            # Should not raise exception
            try:
                self.bot.process_message(update)
            except Exception as e:
                self.fail(f"process_message raised {e} unexpectedly for update: {update}")
    
    def test_extract_language_code(self):
        """Test extracting language code from callback data"""
        # Test direct language code
        result = self.bot._extract_language_code("en")
        self.assertEqual(result, "en")
        
        # Test button text format
        with patch.object(self.bot, '_get_language_code_from_button') as mock_extract:
            mock_extract.return_value = "es"
            result = self.bot._extract_language_code("🇪🇸 Spanish")
            self.assertEqual(result, "es")
            mock_extract.assert_called_once_with("🇪🇸 Spanish")
    
    def test_get_language_from_flag(self):
        """Test getting language code from flag emoji"""
        # Test known flags
        self.assertEqual(self.bot._get_language_from_flag('🇺🇸'), 'en')
        self.assertEqual(self.bot._get_language_from_flag('🇪🇸'), 'es')
        self.assertEqual(self.bot._get_language_from_flag('🇫🇷'), 'fr')
        
        # Test unknown flag
        self.assertIsNone(self.bot._get_language_from_flag('🏳️'))
    
    @patch.object(TelegramBot, 'send_message')
    def test_handle_command_start(self, mock_send):
        """Test handling /start command"""
        self.bot._handle_command(12345, 67890, "/start")
        mock_send.assert_called_once()
        
        # Verify message contains welcome text
        call_args = mock_send.call_args
        message_text = call_args[0][1]  # First positional argument is text
        self.assertIn("Welcome to Language Buddy Bot", message_text)
        self.assertIn("/setpair", message_text)
    
    @patch.object(TelegramBot, 'send_message')
    def test_handle_command_help(self, mock_send):
        """Test handling /help command"""
        self.bot._handle_command(12345, 67890, "/help")
        mock_send.assert_called_once()
        
        # Verify message contains help text
        call_args = mock_send.call_args
        message_text = call_args[0][1]  # First positional argument is text
        self.assertIn("Language Buddy Bot Help", message_text)
        self.assertIn("/setpair", message_text)
    
    @patch.object(TelegramBot, 'send_message')
    def test_handle_command_unknown(self, mock_send):
        """Test handling unknown command"""
        self.bot._handle_command(12345, 67890, "/unknown")
        mock_send.assert_called_once()
        
        # Verify error message
        call_args = mock_send.call_args
        message_text = call_args[0][1]  # First positional argument is text
        self.assertIn("Unknown command", message_text)
        self.assertIn("/help", message_text)


if __name__ == '__main__':
    unittest.main()
