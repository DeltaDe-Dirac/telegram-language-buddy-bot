import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
import os
import json
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.controllers.bot_controller import (
    home, webhook, set_webhook, manual_translate, get_stats, get_voice_status,
    BotSingleton, get_bot
)
from src.main import app


class TestBotController(unittest.TestCase):
    """Test cases for bot controller functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Reset singleton for each test
        BotSingleton._instance = None
        
        # Create Flask test client
        self.client = app.test_client()
        
        # Create Flask app context for testing
        self.app_context = app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Pop Flask app context
        if hasattr(self, 'app_context'):
            self.app_context.pop()
    
    def test_home_endpoint(self):
        """Test home endpoint returns correct structure"""
        result = home()
        
        # Verify structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "active")
        self.assertEqual(result["service"], "Telegram Language Buddy Bot")
        self.assertIn("timestamp", result)
        self.assertEqual(result["version"], "3.0.0")
        
        # Verify timestamp is valid ISO format
        try:
            datetime.fromisoformat(result["timestamp"])
        except ValueError:
            self.fail("Timestamp is not in valid ISO format")
    

    

    

    

    
    def test_bot_singleton_pattern(self):
        """Test that BotSingleton follows singleton pattern"""
        # Create first instance
        singleton1 = BotSingleton()
        self.assertIsNotNone(singleton1)

        # Create second instance
        singleton2 = BotSingleton()

        # Should be the same instance
        self.assertIs(singleton1, singleton2)

    def test_webhook_success(self):
        """Test webhook endpoint with valid update"""
        with app.test_request_context(
            '/webhook',
            method='POST',
            json={"message": {"text": "hello", "chat": {"id": 123}}}
        ):
            with patch('src.controllers.bot_controller.get_bot') as mock_get_bot:
                # Mock bot
                mock_bot = MagicMock()
                mock_get_bot.return_value = mock_bot

                # Call webhook function
                result = webhook()

                # Verify bot.process_message was called
                mock_bot.process_message.assert_called_once()

    def test_webhook_invalid_json(self):
        """Test webhook endpoint with invalid JSON"""
        with app.test_request_context(
            '/webhook',
            method='POST',
            data='invalid json',
            content_type='application/json'
        ):
            with patch('src.controllers.bot_controller.logger') as mock_logger:
                result = webhook()

                # Should return error response
                self.assertIsInstance(result, tuple)
                self.assertEqual(result[1], 400)

    def test_set_webhook_success(self):
        """Test set_webhook endpoint success"""
        with app.test_request_context(
            '/set_webhook',
            method='POST',
            json={"url": "https://example.com/webhook"}
        ):
            with patch('src.controllers.bot_controller.get_bot') as mock_get_bot, \
                 patch('src.controllers.bot_controller.requests.post') as mock_post:

                # Mock bot
                mock_bot = MagicMock()
                mock_bot.base_url = "https://api.telegram.org/bot123"
                mock_get_bot.return_value = mock_bot

                # Mock response
                mock_response = MagicMock()
                mock_response.json.return_value = {"ok": True}
                mock_post.return_value = mock_response

                result = set_webhook()

                # Verify Telegram API was called
                mock_post.assert_called_once_with(
                    "https://api.telegram.org/bot123/setWebhook",
                    json={"url": "https://example.com/webhook"}
                )

    def test_set_webhook_missing_url(self):
        """Test set_webhook endpoint with missing URL"""
        with app.test_request_context(
            '/set_webhook',
            method='POST',
            json={}
        ):
            result = set_webhook()

            # Should return tuple (response, status_code)
            self.assertIsInstance(result, tuple)
            self.assertEqual(result[1], 400)
            self.assertIn("error", result[0].get_json())

    def test_manual_translate_success(self):
        """Test manual_translate endpoint success"""
        with app.test_request_context(
            '/translate',
            method='POST',
            json={
                "text": "Hello world",
                "lang1": "en",
                "lang2": "es"
            }
        ):
            with patch('src.controllers.bot_controller.get_bot') as mock_get_bot:
                # Mock bot and translator
                mock_bot = MagicMock()
                mock_translator = MagicMock()
                mock_translator.detect_language.return_value = "en"
                mock_translator.translate_text.return_value = "Hola mundo"
                mock_bot.translator = mock_translator
                mock_get_bot.return_value = mock_bot

                result = manual_translate()

                # Verify translation was called with correct parameters
                mock_translator.translate_text.assert_called_once_with("Hello world", "es", "en")

    def test_manual_translate_missing_data(self):
        """Test manual_translate endpoint with missing data"""
        with app.test_request_context(
            '/translate',
            method='POST',
            json={"text": None}  # Pass None text to trigger error
        ):
            result = manual_translate()

            # Should return tuple (response, status_code)
            self.assertIsInstance(result, tuple)
            self.assertEqual(result[1], 400)
            self.assertIn("error", result[0].get_json())

    @patch('src.controllers.bot_controller.get_bot')
    def test_get_stats_success(self, mock_get_bot):
        """Test get_stats endpoint success"""
        # Mock bot and database
        mock_bot = MagicMock()
        mock_db = MagicMock()
        mock_db.get_all_preferences.return_value = {"123": ["en", "es"], "456": ["fr", "de"]}
        mock_db.get_session.return_value.__enter__.return_value = MagicMock()
        mock_bot.db = mock_db
        mock_get_bot.return_value = mock_bot

        # Mock UserStats query
        mock_session = MagicMock()
        mock_stats = [MagicMock(translations=10), MagicMock(translations=20)]
        mock_session.query.return_value.all.return_value = mock_stats
        mock_db.get_session.return_value.__enter__.return_value = mock_session

        with patch('src.controllers.bot_controller.jsonify') as mock_jsonify:
            result = get_stats()

            # Verify response structure contains expected keys
            call_args = mock_jsonify.call_args[0][0]
            self.assertIn("total_users", call_args)
            self.assertIn("total_translations", call_args)
            self.assertIn("language_distribution", call_args)

    @patch('src.controllers.bot_controller.get_bot')
    def test_get_stats_database_error(self, mock_get_bot):
        """Test get_stats endpoint with database error"""
        # Mock bot to raise exception
        mock_bot = MagicMock()
        mock_bot.db.get_all_preferences.side_effect = Exception("Database error")
        mock_get_bot.return_value = mock_bot

        result = get_stats()

        # Should return tuple (response, status_code)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result[1], 500)
        self.assertIn("error", result[0].get_json())

    @patch('src.controllers.bot_controller.get_bot')
    def test_get_voice_status_success(self, mock_get_bot):
        """Test get_voice_status endpoint success"""
        # Mock bot and voice transcriber
        mock_bot = MagicMock()
        mock_voice_transcriber = MagicMock()
        mock_voice_transcriber.get_service_status.return_value = {
            "services_available": {"whisper": True, "google": False},
            "total_services": 2,
            "available_services": 1
        }
        mock_bot.voice_transcriber = mock_voice_transcriber
        mock_get_bot.return_value = mock_bot

        with patch('src.controllers.bot_controller.jsonify') as mock_jsonify:
            result = get_voice_status()

            # Verify response includes expected keys
            call_args = mock_jsonify.call_args[0][0]
            self.assertIn("feature_enabled", call_args)
            self.assertIn("total_services", call_args)

    @patch('src.controllers.bot_controller.get_bot')
    def test_get_voice_status_error(self, mock_get_bot):
        """Test get_voice_status endpoint with error"""
        # Mock bot to raise exception
        mock_bot = MagicMock()
        mock_bot.voice_transcriber.get_service_status.side_effect = Exception("Service error")
        mock_get_bot.return_value = mock_bot

        result = get_voice_status()

        # Should return tuple (response, status_code)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result[1], 500)
        self.assertIn("error", result[0].get_json())

    def test_get_bot_function(self):
        """Test get_bot function returns singleton instance"""
        # Reset singleton
        BotSingleton._instance = None

        # Call get_bot
        bot1 = get_bot()
        bot2 = get_bot()

        # Should return same instance (from singleton)
        self.assertIs(bot1, bot2)
        # Should be a TelegramBot instance
        from models.telegram_bot import TelegramBot
        self.assertIsInstance(bot1, TelegramBot)
    



if __name__ == '__main__':
    unittest.main()
