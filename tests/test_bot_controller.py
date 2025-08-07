import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
import os
import json
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.controllers.bot_controller import (
    home, webhook, set_webhook, manual_translate, get_stats,
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
    



if __name__ == '__main__':
    unittest.main()
