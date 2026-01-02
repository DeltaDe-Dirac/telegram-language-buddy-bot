import pytest
from unittest.mock import patch, MagicMock
import os
import sys
import json

# Add the src directory to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.telegram_bot import TelegramBot
from src.models.database import DatabaseManager, Base
from src.models.free_translator import FreeTranslator
from src.models.language_detector import LanguageDetector


@pytest.mark.integration
class TestIntegration:
    """Integration tests for component interactions"""

    @pytest.fixture(autouse=True)
    def setup_database(self, db_session):
        """Set up test database"""
        # Create tables
        Base.metadata.create_all(bind=db_session.bind)
        yield
        # Cleanup is handled by conftest.py clean_database fixture

    def test_bot_database_integration(self, db_session):
        """Test integration between bot and database"""
        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'}):
            # Create bot
            bot = TelegramBot()
            bot.db = DatabaseManager()

            # Test setting and getting user preferences
            chat_id = 12345
            lang1, lang2 = "en", "es"

            # Set preferences through bot
            success = bot.set_user_language_pair(chat_id, lang1, lang2)
            assert success

            # Get preferences through bot
            result = bot.get_user_language_pair(chat_id)
            assert result == (lang1, lang2)

            # Verify in database directly
            db_result = bot.db.get_user_preferences(chat_id)
            assert db_result == (lang1, lang2, 'translation')  # Database returns (lang1, lang2, mode)

    def test_bot_translator_integration(self):
        """Test integration between bot and translator"""
        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'}):
            bot = TelegramBot()

            # Test that bot has translator
            assert isinstance(bot.translator, FreeTranslator)

            # Test language detection through bot
            with patch.object(bot.translator, 'detect_language') as mock_detect:
                mock_detect.return_value = "en"
                detected = bot.translator.detect_language("Hello world")
                assert detected == "en"

    def test_language_detection_validation(self):
        """Test that language detection results are validated"""
        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'}):
            bot = TelegramBot()

            # Test with valid language codes
            valid_languages = ["en", "es", "fr", "de", "ru", "zh"]
            for lang in valid_languages:
                assert LanguageDetector.is_valid_language(lang)

            # Test with invalid language codes
            invalid_languages = ["invalid", "xx", "en-us", ""]
            for lang in invalid_languages:
                assert not LanguageDetector.is_valid_language(lang)

    def test_complete_translation_workflow(self, db_session):
        """Test complete translation workflow"""
        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'}):
            bot = TelegramBot()
            bot.db = DatabaseManager()

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
                    stats = bot.db.get_user_stats(user_id)
                    assert stats is not None
                    assert stats['translations'] == 1

    def test_language_selection_workflow(self, db_session):
        """Test complete language selection workflow"""
        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'}):
            bot = TelegramBot()
            bot.db = DatabaseManager()

            chat_id = 12345

            # Start language selection
            success = bot.db.set_language_selection_state(chat_id, "first_lang")
            assert success

            # Verify state
            state = bot.db.get_language_selection_state(chat_id)
            assert state['step'] == "first_lang"
            assert state['first_lang'] is None

            # Select first language
            success = bot.db.set_language_selection_state(chat_id, "second_lang", "en")
            assert success

            # Verify updated state
            state = bot.db.get_language_selection_state(chat_id)
            assert state['step'] == "second_lang"
            assert state['first_lang'] == "en"

            # Select second language and set preferences
            success = bot.set_user_language_pair(chat_id, "en", "es")
            assert success

            # Clear selection state
            success = bot.db.clear_language_selection_state(chat_id)
            assert success

            # Verify state is cleared
            state = bot.db.get_language_selection_state(chat_id)
            assert state is None

            # Verify preferences are set
            prefs = bot.get_user_language_pair(chat_id)
            assert prefs == ("en", "es")

    def test_message_translation_storage(self, db_session):
        """Test message translation storage and retrieval"""
        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'}):
            bot = TelegramBot()
            bot.db = DatabaseManager()

            chat_id = 12345
            message_id = 67890
            user_id = 11111

            # Store translation
            success = bot.db.store_message_translation(
                chat_id, message_id, user_id,
                "Hello world", "Hola mundo",
                "en", "es"
            )
            assert success

            # Retrieve translation
            translation = bot.db.get_message_translation(chat_id, message_id)
            assert translation is not None
            assert translation['original_text'] == "Hello world"
            assert translation['translated_text'] == "Hola mundo"
            assert translation['source_language'] == "en"
            assert translation['target_language'] == "es"
            assert translation['user_id'] == user_id

    def test_user_stats_integration(self, db_session):
        """Test user statistics integration"""
        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'}):
            bot = TelegramBot()
            bot.db = DatabaseManager()

            user_id = 12345

            # Update stats multiple times
            for i in range(3):
                success = bot.update_user_stats(user_id)
                assert success

            # Verify stats
            stats = bot.db.get_user_stats(user_id)
            assert stats is not None
            assert stats['translations'] == 3
            assert 'joined' in stats
            assert 'last_activity' in stats

    def test_language_keyboard_integration(self):
        """Test language keyboard creation with language validation"""
        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'}):
            bot = TelegramBot()

            # Create keyboard without exclusion
            keyboard = bot._create_language_keyboard()
            assert isinstance(keyboard, list)
            assert len(keyboard) > 0

            # Verify all languages in keyboard are valid
            for row in keyboard:
                for button in row:
                    lang_code = button[1]  # callback_data is language code
                    assert LanguageDetector.is_valid_language(lang_code)

            # Create keyboard with exclusion
            excluded_lang = "en"
            keyboard_excluded = bot._create_language_keyboard(exclude_lang=excluded_lang)

            # Verify excluded language is not present
            for row in keyboard_excluded:
                for button in row:
                    lang_code = button[1]
                    assert lang_code != excluded_lang

    def test_error_handling_integration(self, db_session):
        """Test error handling across components"""
        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'}):
            bot = TelegramBot()
            bot.db = DatabaseManager()

            # Test invalid language pair
            success = bot.set_user_language_pair(12345, "invalid", "en")
            assert not success

            # Test same language pair
            success = bot.set_user_language_pair(12345, "en", "en")
            assert not success

    def test_concurrent_user_management(self, db_session):
        """Test managing multiple users concurrently"""
        with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token_123'}):
            bot = TelegramBot()
            bot.db = DatabaseManager()

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
                assert success

            # Verify all users have correct preferences
            for chat_id, lang1, lang2 in users:
                result = bot.get_user_language_pair(chat_id)
                assert result == (lang1, lang2)

            # Get all preferences
            all_prefs = bot.db.get_all_preferences()
            assert len(all_prefs) == len(users)

            # Verify each user is present
            for chat_id, lang1, lang2 in users:
                assert chat_id in all_prefs
                assert all_prefs[chat_id] == (lang1, lang2, 'translation')  # Database returns (lang1, lang2, mode)
