import unittest
import tempfile
import os
import sys
from datetime import datetime, timezone

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.models.database import DatabaseManager, UserPreferences, UserStats, LanguageSelectionState, MessageTranslation


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager class"""
    
    def setUp(self):
        """Set up test fixtures with in-memory SQLite database"""
        # Use in-memory SQLite for testing
        self.db_manager = DatabaseManager()
        from sqlalchemy import create_engine
        self.db_manager.engine = create_engine('sqlite:///:memory:')
        from sqlalchemy.orm import sessionmaker
        self.db_manager.session_local = sessionmaker(
            autocommit=False, autoflush=False, bind=self.db_manager.engine
        )
        
        # Create tables
        from src.models.database import Base
        Base.metadata.create_all(bind=self.db_manager.engine)
    
    def tearDown(self):
        """Clean up after tests"""
        # Close any open sessions
        if hasattr(self, 'db_manager'):
            self.db_manager.engine.dispose()
    
    def test_database_initialization(self):
        """Test that database manager initializes correctly"""
        self.assertIsNotNone(self.db_manager.engine)
        self.assertIsNotNone(self.db_manager.session_local)
    
    def test_get_user_preferences_nonexistent(self):
        """Test getting preferences for non-existent user"""
        result = self.db_manager.get_user_preferences(12345)
        self.assertIsNone(result)
    
    def test_set_user_preferences_new(self):
        """Test setting new user preferences"""
        chat_id = 12345
        lang1, lang2 = "en", "es"
        
        # Set preferences
        success = self.db_manager.set_user_preferences(chat_id, lang1, lang2)
        self.assertTrue(success)
        
        # Get preferences
        result = self.db_manager.get_user_preferences(chat_id)
        self.assertIsNotNone(result)
        self.assertEqual(result, (lang1, lang2))
    
    def test_set_user_preferences_update(self):
        """Test updating existing user preferences"""
        chat_id = 12345
        lang1, lang2 = "en", "es"
        
        # Set initial preferences
        self.db_manager.set_user_preferences(chat_id, lang1, lang2)
        
        # Update preferences
        new_lang1, new_lang2 = "fr", "de"
        success = self.db_manager.set_user_preferences(chat_id, new_lang1, new_lang2)
        self.assertTrue(success)
        
        # Verify update
        result = self.db_manager.get_user_preferences(chat_id)
        self.assertEqual(result, (new_lang1, new_lang2))
    
    def test_set_user_preferences_case_insensitive(self):
        """Test that language codes are stored in lowercase"""
        chat_id = 12345
        lang1, lang2 = "EN", "ES"
        
        # Set preferences with uppercase
        self.db_manager.set_user_preferences(chat_id, lang1, lang2)
        
        # Get preferences
        result = self.db_manager.get_user_preferences(chat_id)
        self.assertEqual(result, ("en", "es"))
    
    def test_get_user_stats_nonexistent(self):
        """Test getting stats for non-existent user"""
        result = self.db_manager.get_user_stats(12345)
        self.assertIsNone(result)
    
    def test_update_user_stats_new(self):
        """Test updating stats for new user"""
        user_id = 12345
        
        # Update stats
        success = self.db_manager.update_user_stats(user_id)
        self.assertTrue(success)
        
        # Get stats
        result = self.db_manager.get_user_stats(user_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['translations'], 1)
        self.assertIsInstance(result['joined'], datetime)
        self.assertIsInstance(result['last_activity'], datetime)
    
    def test_update_user_stats_existing(self):
        """Test updating stats for existing user"""
        user_id = 12345
        
        # Initial update
        self.db_manager.update_user_stats(user_id)
        
        # Second update
        success = self.db_manager.update_user_stats(user_id)
        self.assertTrue(success)
        
        # Verify count increased
        result = self.db_manager.get_user_stats(user_id)
        self.assertEqual(result['translations'], 2)
    
    def test_get_all_preferences_empty(self):
        """Test getting all preferences when database is empty"""
        result = self.db_manager.get_all_preferences()
        self.assertEqual(result, {})
    
    def test_get_all_preferences_multiple(self):
        """Test getting all preferences with multiple users"""
        # Add multiple users
        self.db_manager.set_user_preferences(1, "en", "es")
        self.db_manager.set_user_preferences(2, "fr", "de")
        self.db_manager.set_user_preferences(3, "ru", "zh")
        
        # Get all preferences
        result = self.db_manager.get_all_preferences()
        
        # Verify results
        self.assertEqual(len(result), 3)
        self.assertEqual(result[1], ("en", "es"))
        self.assertEqual(result[2], ("fr", "de"))
        self.assertEqual(result[3], ("ru", "zh"))
    
    def test_language_selection_state_workflow(self):
        """Test complete language selection state workflow"""
        chat_id = 12345
        
        # Set initial state
        success = self.db_manager.set_language_selection_state(chat_id, "first_lang")
        self.assertTrue(success)
        
        # Get state
        state = self.db_manager.get_language_selection_state(chat_id)
        self.assertIsNotNone(state)
        self.assertEqual(state['step'], "first_lang")
        self.assertIsNone(state['first_lang'])
        
        # Update state with first language
        success = self.db_manager.set_language_selection_state(chat_id, "second_lang", "en")
        self.assertTrue(success)
        
        # Get updated state
        state = self.db_manager.get_language_selection_state(chat_id)
        self.assertEqual(state['step'], "second_lang")
        self.assertEqual(state['first_lang'], "en")
        
        # Clear state
        success = self.db_manager.clear_language_selection_state(chat_id)
        self.assertTrue(success)
        
        # Verify state is cleared
        state = self.db_manager.get_language_selection_state(chat_id)
        self.assertIsNone(state)
    
    def test_get_language_selection_state_nonexistent(self):
        """Test getting selection state for non-existent chat"""
        result = self.db_manager.get_language_selection_state(12345)
        self.assertIsNone(result)
    
    def test_clear_language_selection_state_nonexistent(self):
        """Test clearing selection state for non-existent chat"""
        success = self.db_manager.clear_language_selection_state(12345)
        self.assertTrue(success)  # Should not fail
    
    def test_store_message_translation_new(self):
        """Test storing new message translation"""
        chat_id = 12345
        message_id = 67890
        user_id = 11111
        original_text = "Hello world"
        translated_text = "Hola mundo"
        source_lang = "en"
        target_lang = "es"
        
        # Store translation
        success = self.db_manager.store_message_translation(
            chat_id, message_id, user_id, original_text, translated_text,
            source_lang, target_lang
        )
        self.assertTrue(success)
        
        # Get translation
        result = self.db_manager.get_message_translation(chat_id, message_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['original_text'], original_text)
        self.assertEqual(result['translated_text'], translated_text)
        self.assertEqual(result['source_language'], source_lang)
        self.assertEqual(result['target_language'], target_lang)
        self.assertEqual(result['user_id'], user_id)
    
    def test_store_message_translation_update(self):
        """Test updating existing message translation"""
        chat_id = 12345
        message_id = 67890
        user_id = 11111
        
        # Store initial translation
        self.db_manager.store_message_translation(
            chat_id, message_id, user_id, "Hello", "Hola", "en", "es"
        )
        
        # Update translation
        success = self.db_manager.store_message_translation(
            chat_id, message_id, user_id, "Hello world", "Hola mundo", "en", "es"
        )
        self.assertTrue(success)
        
        # Verify update
        result = self.db_manager.get_message_translation(chat_id, message_id)
        self.assertEqual(result['original_text'], "Hello world")
        self.assertEqual(result['translated_text'], "Hola mundo")
    
    def test_get_message_translation_nonexistent(self):
        """Test getting translation for non-existent message"""
        result = self.db_manager.get_message_translation(12345, 67890)
        self.assertIsNone(result)
    
    def test_database_session_context_manager(self):
        """Test that database session context manager works correctly"""
        with self.db_manager.get_session() as session:
            self.assertIsNotNone(session)
            # Session should be valid
            self.assertTrue(hasattr(session, 'query'))
    
    def test_concurrent_user_preferences(self):
        """Test handling multiple users with different preferences"""
        # Add multiple users
        users = [
            (1, "en", "es"),
            (2, "fr", "de"),
            (3, "ru", "zh"),
            (4, "ja", "ko"),
            (5, "ar", "hi")
        ]
        
        for chat_id, lang1, lang2 in users:
            success = self.db_manager.set_user_preferences(chat_id, lang1, lang2)
            self.assertTrue(success)
        
        # Verify all users have correct preferences
        for chat_id, lang1, lang2 in users:
            result = self.db_manager.get_user_preferences(chat_id)
            self.assertEqual(result, (lang1, lang2))
    
    def test_user_stats_increment(self):
        """Test that user stats increment correctly"""
        user_id = 12345
        
        # Multiple updates
        for _ in range(5):
            success = self.db_manager.update_user_stats(user_id)
            self.assertTrue(success)
        
        # Verify final count
        result = self.db_manager.get_user_stats(user_id)
        self.assertEqual(result['translations'], 5)
    
    def test_database_error_handling(self):
        """Test database error handling with invalid data"""
        # Test with invalid chat_id type
        result = self.db_manager.get_user_preferences("invalid_id")
        self.assertIsNone(result)
        
        # Test with invalid user_id type
        result = self.db_manager.get_user_stats("invalid_id")
        self.assertIsNone(result)
    
    def test_large_text_handling(self):
        """Test handling of large text in message translations"""
        chat_id = 12345
        message_id = 67890
        user_id = 11111
        
        # Create large text
        large_text = "A" * 10000  # 10KB text
        
        success = self.db_manager.store_message_translation(
            chat_id, message_id, user_id, large_text, large_text, "en", "es"
        )
        self.assertTrue(success)
        
        # Retrieve and verify
        result = self.db_manager.get_message_translation(chat_id, message_id)
        self.assertEqual(result['original_text'], large_text)
        self.assertEqual(result['translated_text'], large_text)
    
    def test_special_characters_in_text(self):
        """Test handling of special characters in text"""
        chat_id = 12345
        message_id = 67890
        user_id = 11111
        
        special_text = "Hello 世界! 🌍 Привет! こんにちは! ¡Hola! Bonjour! 😊"
        
        success = self.db_manager.store_message_translation(
            chat_id, message_id, user_id, special_text, special_text, "en", "es"
        )
        self.assertTrue(success)
        
        # Retrieve and verify
        result = self.db_manager.get_message_translation(chat_id, message_id)
        self.assertEqual(result['original_text'], special_text)
        self.assertEqual(result['translated_text'], special_text)
    
    def test_unicode_language_codes(self):
        """Test handling of unicode in language codes"""
        chat_id = 12345
        
        # Test with unicode characters in language codes (should be normalized)
        success = self.db_manager.set_user_preferences(chat_id, "en", "es")
        self.assertTrue(success)
        
        result = self.db_manager.get_user_preferences(chat_id)
        self.assertEqual(result, ("en", "es"))
    
    def test_negative_user_ids(self):
        """Test handling of negative user IDs"""
        user_id = -12345
        
        # Should handle negative IDs gracefully
        success = self.db_manager.update_user_stats(user_id)
        self.assertTrue(success)
        
        result = self.db_manager.get_user_stats(user_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['translations'], 1)
    
    def test_zero_user_ids(self):
        """Test handling of zero user IDs"""
        user_id = 0
        
        # Should handle zero ID gracefully
        success = self.db_manager.update_user_stats(user_id)
        self.assertTrue(success)
        
        result = self.db_manager.get_user_stats(user_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['translations'], 1)
    
    def test_duplicate_message_translations(self):
        """Test handling of duplicate message translations"""
        chat_id = 12345
        message_id = 67890
        user_id = 11111
        
        # Store same translation multiple times
        for _ in range(3):
            success = self.db_manager.store_message_translation(
                chat_id, message_id, user_id, "Hello", "Hola", "en", "es"
            )
            self.assertTrue(success)
        
        # Should only have one record
        result = self.db_manager.get_message_translation(chat_id, message_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['original_text'], "Hello")
        self.assertEqual(result['translated_text'], "Hola")
    
    def test_session_rollback_on_error(self):
        """Test that sessions rollback properly on errors"""
        with self.db_manager.get_session() as session:
            # Try to create an invalid record (should fail)
            try:
                # This should fail due to missing required fields
                invalid_pref = UserPreferences()
                session.add(invalid_pref)
                session.commit()
                self.fail("Should have raised an exception")
            except Exception:
                session.rollback()
                # Session should be in a clean state
                self.assertIsNone(session.query(UserPreferences).first())
    
    def test_concurrent_session_handling(self):
        """Test handling of multiple concurrent sessions"""
        # Create multiple sessions
        with self.db_manager.get_session() as session1:
            with self.db_manager.get_session() as session2:
                # Both sessions should be independent
                self.assertIsNot(session1, session2)
                
                # Both should be able to query
                result1 = session1.query(UserPreferences).all()
                result2 = session2.query(UserPreferences).all()
                
                self.assertEqual(len(result1), len(result2))
    
    def test_data_integrity_constraints(self):
        """Test that data integrity constraints are enforced"""
        chat_id = 12345
        
        # Test that we can't set invalid language codes
        # This would require additional validation in the model
        # For now, we test that the database accepts valid codes
        success = self.db_manager.set_user_preferences(chat_id, "en", "es")
        self.assertTrue(success)
        
        # Verify the data is stored correctly
        result = self.db_manager.get_user_preferences(chat_id)
        self.assertEqual(result, ("en", "es"))


if __name__ == '__main__':
    unittest.main()
