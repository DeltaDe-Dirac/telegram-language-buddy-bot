import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
import os
import json
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from controllers.bot_controller import (
    home, webhook, set_webhook, manual_translate, get_stats,
    BotSingleton, get_bot
)


class TestBotController(unittest.TestCase):
    """Test cases for bot controller functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Reset singleton for each test
        BotSingleton._instance = None
    
    def test_home_endpoint(self):
        """Test home endpoint returns correct structure"""
        result = home()
        
        # Verify structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "active")
        self.assertEqual(result["service"], "Telegram Language Buddy Bot")
        self.assertIn("timestamp", result)
        self.assertEqual(result["version"], "1.0.0")
        
        # Verify timestamp is valid ISO format
        try:
            datetime.fromisoformat(result["timestamp"])
        except ValueError:
            self.fail("Timestamp is not in valid ISO format")
    
    @patch('controllers.bot_controller.get_bot')
    def test_webhook_success(self, mock_get_bot):
        """Test successful webhook processing"""
        # Mock bot
        mock_bot = MagicMock()
        mock_get_bot.return_value = mock_bot
        
        # Mock request
        mock_request = MagicMock()
        mock_request.get_json.return_value = {
            "message": {
                "chat": {"id": 12345},
                "from": {"id": 67890, "first_name": "Test"},
                "text": "Hello"
            }
        }
        
        with patch('controllers.bot_controller.request', mock_request):
            with patch('controllers.bot_controller.jsonify') as mock_jsonify:
                mock_jsonify.return_value = {"ok": True}
                
                result = webhook()
                
                # Verify bot was called
                mock_bot.process_message.assert_called_once()
                mock_jsonify.assert_called_with({"ok": True})
    
    @patch('controllers.bot_controller.get_bot')
    def test_webhook_invalid_json(self, mock_get_bot):
        """Test webhook with invalid JSON"""
        # Mock request with invalid JSON
        mock_request = MagicMock()
        mock_request.get_json.side_effect = ValueError("Invalid JSON")
        
        with patch('controllers.bot_controller.request', mock_request):
            with patch('controllers.bot_controller.jsonify') as mock_jsonify:
                mock_jsonify.return_value = {"ok": False, "error": "Invalid JSON"}
                
                result = webhook()
                
                # Verify error response
                mock_jsonify.assert_called_with({"ok": False, "error": "Invalid JSON"})
    
    @patch('controllers.bot_controller.get_bot')
    def test_webhook_missing_data(self, mock_get_bot):
        """Test webhook with missing data"""
        # Mock request with missing data
        mock_request = MagicMock()
        mock_request.get_json.return_value = {}
        
        with patch('controllers.bot_controller.request', mock_request):
            with patch('controllers.bot_controller.jsonify') as mock_jsonify:
                mock_jsonify.return_value = {"ok": True}
                
                result = webhook()
                
                # Should still process (bot handles empty data)
                mock_get_bot.return_value.process_message.assert_called_once_with({})
    
    @patch('controllers.bot_controller.get_bot')
    @patch('controllers.bot_controller.requests.post')
    def test_set_webhook_success(self, mock_post, mock_get_bot):
        """Test successful webhook setting"""
        # Mock bot
        mock_bot = MagicMock()
        mock_bot.base_url = "https://api.telegram.org/bottest_token"
        mock_get_bot.return_value = mock_bot
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True, "result": True}
        mock_post.return_value = mock_response
        
        # Mock request
        mock_request = MagicMock()
        mock_request.json = {"url": "https://example.com/webhook"}
        
        with patch('controllers.bot_controller.request', mock_request):
            with patch('controllers.bot_controller.jsonify') as mock_jsonify:
                mock_jsonify.return_value = {"ok": True, "result": True}
                
                result = set_webhook()
                
                # Verify request was made
                mock_post.assert_called_once_with(
                    "https://api.telegram.org/bottest_token/setWebhook",
                    json={"url": "https://example.com/webhook"}
                )
                mock_jsonify.assert_called_with({"ok": True, "result": True})
    
    @patch('controllers.bot_controller.get_bot')
    def test_set_webhook_missing_url(self, mock_get_bot):
        """Test set_webhook with missing URL"""
        # Mock request without URL
        mock_request = MagicMock()
        mock_request.json = {}
        
        with patch('controllers.bot_controller.request', mock_request):
            with patch('controllers.bot_controller.jsonify') as mock_jsonify:
                mock_jsonify.return_value = {"error": "URL is required"}
                
                result = set_webhook()
                
                # Verify error response
                mock_jsonify.assert_called_with({"error": "URL is required"})
    
    @patch('controllers.bot_controller.get_bot')
    @patch('controllers.bot_controller.requests.post')
    def test_set_webhook_request_exception(self, mock_post, mock_get_bot):
        """Test set_webhook with request exception"""
        # Mock bot
        mock_bot = MagicMock()
        mock_bot.base_url = "https://api.telegram.org/bottest_token"
        mock_get_bot.return_value = mock_bot
        
        # Mock request exception
        from requests import RequestException
        mock_post.side_effect = RequestException("Network error")
        
        # Mock request
        mock_request = MagicMock()
        mock_request.json = {"url": "https://example.com/webhook"}
        
        with patch('controllers.bot_controller.request', mock_request):
            with patch('controllers.bot_controller.jsonify') as mock_jsonify:
                result = set_webhook()
                
                # Verify error response
                mock_jsonify.assert_called()
    
    @patch('controllers.bot_controller.get_bot')
    def test_manual_translate_success(self, mock_get_bot):
        """Test successful manual translation"""
        # Mock bot and translator
        mock_bot = MagicMock()
        mock_translator = MagicMock()
        mock_bot.translator = mock_translator
        mock_translator.detect_language.return_value = "en"
        mock_translator.translate_text.return_value = "Hola mundo"
        mock_get_bot.return_value = mock_bot
        
        # Mock request
        mock_request = MagicMock()
        mock_request.get_json.return_value = {
            "text": "Hello world",
            "lang1": "en",
            "lang2": "es"
        }
        
        with patch('controllers.bot_controller.request', mock_request):
            with patch('controllers.bot_controller.jsonify') as mock_jsonify:
                mock_jsonify.return_value = {
                    "original": "Hello world",
                    "translated": "Hola mundo",
                    "source_language": "en",
                    "target_language": "es",
                    "language_pair": "en ↔ es"
                }
                
                result = manual_translate()
                
                # Verify translation was called
                mock_translator.detect_language.assert_called_once_with("Hello world")
                mock_translator.translate_text.assert_called_once_with("Hello world", "es", "en")
                
                # Verify response structure
                expected_response = {
                    "original": "Hello world",
                    "translated": "Hola mundo",
                    "source_language": "en",
                    "target_language": "es",
                    "language_pair": "en ↔ es"
                }
                mock_jsonify.assert_called_with(expected_response)
    
    @patch('controllers.bot_controller.get_bot')
    def test_manual_translate_auto_detection(self, mock_get_bot):
        """Test manual translation with auto language detection"""
        # Mock bot and translator
        mock_bot = MagicMock()
        mock_translator = MagicMock()
        mock_bot.translator = mock_translator
        mock_translator.detect_language.return_value = "fr"
        mock_translator.translate_text.return_value = "Hello world"
        mock_get_bot.return_value = mock_bot
        
        # Mock request without lang1 (should use detected language)
        mock_request = MagicMock()
        mock_request.get_json.return_value = {
            "text": "Bonjour le monde",
            "lang2": "en"
        }
        
        with patch('controllers.bot_controller.request', mock_request):
            with patch('controllers.bot_controller.jsonify') as mock_jsonify:
                result = manual_translate()
                
                # Verify translation used detected language
                mock_translator.translate_text.assert_called_once_with("Bonjour le monde", "en", "fr")
    
    @patch('controllers.bot_controller.get_bot')
    def test_manual_translate_missing_text(self, mock_get_bot):
        """Test manual translation with missing text"""
        # Mock request without text
        mock_request = MagicMock()
        mock_request.get_json.return_value = {"lang1": "en", "lang2": "es"}
        
        with patch('controllers.bot_controller.request', mock_request):
            with patch('controllers.bot_controller.jsonify') as mock_jsonify:
                result = manual_translate()
                
                # Verify that the function handles missing text gracefully
                # The function should still return a response even with missing text
                mock_jsonify.assert_called()
    
    @patch('controllers.bot_controller.get_bot')
    def test_get_stats_success(self, mock_get_bot):
        """Test successful stats retrieval"""
        # Mock bot and database
        mock_bot = MagicMock()
        mock_db = MagicMock()
        mock_bot.db = mock_db
        
        # Mock database responses
        mock_db.get_all_preferences.return_value = {
            12345: ("en", "es"),
            67890: ("fr", "de")
        }
        
        # Mock session context manager
        mock_session = MagicMock()
        mock_db.get_session.return_value.__enter__.return_value = mock_session
        
        # Mock UserStats query
        from models.database import UserStats
        mock_stats = [
            MagicMock(translations=5),
            MagicMock(translations=3)
        ]
        mock_session.query.return_value.all.return_value = mock_stats
        
        mock_get_bot.return_value = mock_bot
        
        with patch('controllers.bot_controller.jsonify') as mock_jsonify:
            result = get_stats()
            
            # Verify database calls
            mock_db.get_all_preferences.assert_called_once()
            mock_db.get_session.assert_called_once()
            
            # Verify response structure - check that jsonify was called with the right structure
            mock_jsonify.assert_called_once()
            call_args = mock_jsonify.call_args[0][0]
            
            # Verify expected keys are present
            self.assertIn("total_users", call_args)
            self.assertIn("total_translations", call_args)
            self.assertIn("language_distribution", call_args)
            self.assertIn("supported_languages", call_args)
            self.assertIn("preferences_by_chat", call_args)
            self.assertIn("storage_type", call_args)
            self.assertIn("database_url", call_args)
            
            # Verify expected values
            self.assertEqual(call_args["total_users"], 2)
            self.assertEqual(call_args["total_translations"], 8)
            self.assertEqual(call_args["language_distribution"], {"en": 1, "es": 1, "fr": 1, "de": 1})
            self.assertEqual(call_args["preferences_by_chat"], {"12345": ("en", "es"), "67890": ("fr", "de")})
            self.assertEqual(call_args["storage_type"], "database")
    
    @patch('controllers.bot_controller.get_bot')
    def test_get_stats_empty_database(self, mock_get_bot):
        """Test stats retrieval with empty database"""
        # Mock bot and database
        mock_bot = MagicMock()
        mock_db = MagicMock()
        mock_bot.db = mock_db
        
        # Mock empty database
        mock_db.get_all_preferences.return_value = {}
        mock_db.get_session.return_value.__enter__.return_value.query.return_value.all.return_value = []
        
        mock_get_bot.return_value = mock_bot
        
        with patch('controllers.bot_controller.jsonify') as mock_jsonify:
            result = get_stats()
            
            # Verify response has zero values
            call_args = mock_jsonify.call_args[0][0]
            self.assertEqual(call_args["total_users"], 0)
            self.assertEqual(call_args["total_translations"], 0)
            self.assertEqual(call_args["language_distribution"], {})
    
    def test_bot_singleton_pattern(self):
        """Test that BotSingleton follows singleton pattern"""
        # Create first instance
        singleton1 = BotSingleton()
        self.assertIsNotNone(singleton1)
        
        # Create second instance
        singleton2 = BotSingleton()
        
        # Should be the same instance
        self.assertIs(singleton1, singleton2)
    
    @patch('controllers.bot_controller.TelegramBot')
    def test_get_bot_creates_instance(self, mock_telegram_bot_class):
        """Test that get_bot creates TelegramBot instance"""
        # Mock TelegramBot class
        mock_bot_instance = MagicMock()
        mock_telegram_bot_class.return_value = mock_bot_instance
        
        # Reset singleton
        BotSingleton._instance = None
        
        # Get bot
        result = get_bot()
        
        # Verify TelegramBot was created
        mock_telegram_bot_class.assert_called_once()
        self.assertEqual(result, mock_bot_instance)
    
    @patch('controllers.bot_controller.TelegramBot')
    def test_get_bot_reuses_instance(self, mock_telegram_bot_class):
        """Test that get_bot reuses existing instance"""
        # Mock TelegramBot class
        mock_bot_instance = MagicMock()
        mock_telegram_bot_class.return_value = mock_bot_instance
        
        # Reset singleton
        BotSingleton._instance = None
        
        # Get bot twice
        result1 = get_bot()
        result2 = get_bot()
        
        # Verify both results are the same instance
        self.assertEqual(result1, result2)
        # Verify that the same mock instance is returned
        self.assertIs(result1, result2)


if __name__ == '__main__':
    unittest.main()
