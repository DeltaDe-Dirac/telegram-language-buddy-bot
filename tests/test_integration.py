import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models.telegram_bot import TelegramBot
from models.database import DatabaseManager
from models.free_translator import FreeTranslator
from models.language_detector import LanguageDetector


class TestIntegration(unittest.TestCase):
    """Integration tests for component interactions"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Use in-memory database for testing
        self.db_manager = DatabaseManager()
        from sqlalchemy import create_engine
        self.db_manager.engine = create_engine('sqlite:///:memory:')
        from sqlalchemy.orm import sessionmaker
        self.db_manager.session_local = sessionmaker(
            autocommit=False, autoflush=False, bind=self.db_manager.engine
        )
        
        # Create tables
        from models.database import Base
        Base.metadata.create_all(bind=self.db_manager.engine)
        
        # Create translator
        self.translator = FreeTranslator()
    
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'db_manager'):
            self.db_manager.engine.dispose()
    
    @patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'})
    def test_bot_database_integration(self):
        """Test integration between bot and database"""
        # Create bot with our test database
        bot = TelegramBot()
        bot.db = self.db_manager
        
        # Test setting and getting user preferences
        chat_id = 12345
        lang1, lang2 = "en", "es"
        
        # Set preferences through bot
        success = bot.set_user_language_pair(chat_id, lang1, lang2)
        self.assertTrue(success)
        
        # Get preferences through bot
        result = bot.get_user_language_pair(chat_id)
        self.assertEqual(result, (lang1, lang2))
        
        # Verify in database directly
        db_result = self.db_manager.get_user_preferences(chat_id)
        self.assertEqual(db_result, (lang1, lang2))
    
    @patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'})
    def test_bot_translator_integration(self):
        """Test integration between bot and translator"""
        bot = TelegramBot()
        
        # Test that bot has translator
        self.assertIsInstance(bot.translator, FreeTranslator)
        
        # Test language detection through bot
        with patch.object(bot.translator, 'detect_language') as mock_detect:
            mock_detect.return_value = "en"
            detected = bot.translator.detect_language("Hello world")
            self.assertEqual(detected, "en")
    
    @patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'})
    def test_language_detection_validation(self):
        """Test that language detection results are validated"""
        bot = TelegramBot()
        
        # Test with valid language codes
        valid_languages = ["en", "es", "fr", "de", "ru", "zh"]
        for lang in valid_languages:
            self.assertTrue(LanguageDetector.is_valid_language(lang))
        
        # Test with invalid language codes
        invalid_languages = ["invalid", "xx", "en-us", ""]
        for lang in invalid_languages:
            self.assertFalse(LanguageDetector.is_valid_language(lang))
    
    @patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'})
    def test_complete_translation_workflow(self):
        """Test complete translation workflow"""
        bot = TelegramBot()
        bot.db = self.db_manager
        
        # Set up user preferences
        chat_id = 12345
        user_id = 67890
        bot.set_user_language_pair(chat_id, "en", "es")
        
        # Mock translation
        with patch.object(bot.translator, 'detect_language') as mock_detect:
            with patch.object(bot.translator, 'translate_text') as mock_translate:
                mock_detect.return_value = "en"
                mock_translate.return_value = "Hola mundo"
                
                # Simulate message processing
                message = {
                    "chat": {"id": chat_id},
                    "from": {"id": user_id, "first_name": "Test"},
                    "text": "Hello world",
                    "message_id": 123
                }
                
                # Process message
                bot._handle_message(message)
                
                # Verify language detection was called
                mock_detect.assert_called_once_with("Hello world", allowed_langs=("en", "es"))
                
                # Verify translation was called
                mock_translate.assert_called_once_with("Hello world", "es", "en")
                
                # Verify user stats were updated
                stats = self.db_manager.get_user_stats(user_id)
                self.assertIsNotNone(stats)
                self.assertEqual(stats['translations'], 1)
    
    @patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'})
    def test_language_selection_workflow(self):
        """Test complete language selection workflow"""
        bot = TelegramBot()
        bot.db = self.db_manager
        
        chat_id = 12345
        
        # Start language selection
        success = self.db_manager.set_language_selection_state(chat_id, "first_lang")
        self.assertTrue(success)
        
        # Verify state
        state = self.db_manager.get_language_selection_state(chat_id)
        self.assertEqual(state['step'], "first_lang")
        self.assertIsNone(state['first_lang'])
        
        # Select first language
        success = self.db_manager.set_language_selection_state(chat_id, "second_lang", "en")
        self.assertTrue(success)
        
        # Verify updated state
        state = self.db_manager.get_language_selection_state(chat_id)
        self.assertEqual(state['step'], "second_lang")
        self.assertEqual(state['first_lang'], "en")
        
        # Select second language and set preferences
        success = bot.set_user_language_pair(chat_id, "en", "es")
        self.assertTrue(success)
        
        # Clear selection state
        success = self.db_manager.clear_language_selection_state(chat_id)
        self.assertTrue(success)
        
        # Verify state is cleared
        state = self.db_manager.get_language_selection_state(chat_id)
        self.assertIsNone(state)
        
        # Verify preferences are set
        prefs = bot.get_user_language_pair(chat_id)
        self.assertEqual(prefs, ("en", "es"))
    
    @patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'})
    def test_message_translation_storage(self):
        """Test message translation storage and retrieval"""
        bot = TelegramBot()
        bot.db = self.db_manager
        
        chat_id = 12345
        message_id = 67890
        user_id = 11111
        
        # Store translation
        success = self.db_manager.store_message_translation(
            chat_id, message_id, user_id,
            "Hello world", "Hola mundo",
            "en", "es"
        )
        self.assertTrue(success)
        
        # Retrieve translation
        translation = self.db_manager.get_message_translation(chat_id, message_id)
        self.assertIsNotNone(translation)
        self.assertEqual(translation['original_text'], "Hello world")
        self.assertEqual(translation['translated_text'], "Hola mundo")
        self.assertEqual(translation['source_language'], "en")
        self.assertEqual(translation['target_language'], "es")
        self.assertEqual(translation['user_id'], user_id)
    
    @patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'})
    def test_user_stats_integration(self):
        """Test user statistics integration"""
        bot = TelegramBot()
        bot.db = self.db_manager
        
        user_id = 12345
        
        # Update stats multiple times
        for i in range(3):
            success = bot.update_user_stats(user_id)
            self.assertTrue(success)
        
        # Verify stats
        stats = bot.db.get_user_stats(user_id)
        self.assertIsNotNone(stats)
        self.assertEqual(stats['translations'], 3)
        self.assertIsInstance(stats['joined'], type(bot.db.get_user_stats(user_id)['joined']))
        self.assertIsInstance(stats['last_activity'], type(bot.db.get_user_stats(user_id)['last_activity']))
    
    @patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'})
    def test_language_keyboard_integration(self):
        """Test language keyboard creation with language validation"""
        bot = TelegramBot()
        
        # Create keyboard without exclusion
        keyboard = bot._create_language_keyboard()
        self.assertIsInstance(keyboard, list)
        self.assertGreater(len(keyboard), 0)
        
        # Verify all languages in keyboard are valid
        for row in keyboard:
            for button in row:
                lang_code = button[1]  # callback_data is language code
                self.assertTrue(LanguageDetector.is_valid_language(lang_code))
        
        # Create keyboard with exclusion
        excluded_lang = "en"
        keyboard_excluded = bot._create_language_keyboard(exclude_lang=excluded_lang)
        
        # Verify excluded language is not present
        for row in keyboard_excluded:
            for button in row:
                lang_code = button[1]
                self.assertNotEqual(lang_code, excluded_lang)
    
    @patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'})
    def test_error_handling_integration(self):
        """Test error handling across components"""
        bot = TelegramBot()
        bot.db = self.db_manager
        
        # Test invalid language pair
        success = bot.set_user_language_pair(12345, "invalid", "en")
        self.assertFalse(success)
        
        # Test same language pair
        success = bot.set_user_language_pair(12345, "en", "en")
        self.assertFalse(success)
        
        # Test invalid chat_id type
        result = bot.db.get_user_preferences("invalid_id")
        self.assertIsNone(result)
        
        # Test invalid user_id type
        result = bot.db.get_user_stats("invalid_id")
        self.assertIsNone(result)
    
    @patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'})
    def test_concurrent_user_management(self):
        """Test managing multiple users concurrently"""
        bot = TelegramBot()
        bot.db = self.db_manager
        
        # Create multiple users with different preferences
        users = [
            (1, "en", "es"),
            (2, "fr", "de"),
            (3, "ru", "zh"),
            (4, "ja", "ko"),
            (5, "ar", "hi")
        ]
        
        # Set preferences for all users
        for chat_id, lang1, lang2 in users:
            success = bot.set_user_language_pair(chat_id, lang1, lang2)
            self.assertTrue(success)
        
        # Verify all users have correct preferences
        for chat_id, lang1, lang2 in users:
            result = bot.get_user_language_pair(chat_id)
            self.assertEqual(result, (lang1, lang2))
        
        # Get all preferences
        all_prefs = bot.db.get_all_preferences()
        self.assertEqual(len(all_prefs), len(users))
        
        # Verify each user is present
        for chat_id, lang1, lang2 in users:
            self.assertIn(chat_id, all_prefs)
            self.assertEqual(all_prefs[chat_id], (lang1, lang2))


if __name__ == '__main__':
    unittest.main()
