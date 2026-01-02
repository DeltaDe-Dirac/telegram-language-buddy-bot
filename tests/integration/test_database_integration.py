import pytest
import sys
import os
from sqlalchemy import text

# Add the src directory to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database operations"""

    def test_database_connection(self, db_session):
        """Test that we can connect to the database and execute queries"""
        result = db_session.execute(text("SELECT 1 as test_value"))
        row = result.fetchone()
        assert row[0] == 1

    def test_user_preferences_operations(self, db_session):
        """Test user preferences CRUD operations"""
        from src.models.database import DatabaseManager

        # Initialize database manager
        db_manager = DatabaseManager()

        # Test setting preferences
        chat_id = 12345
        success = db_manager.set_user_preferences(chat_id, 'en', 'es')
        assert success

        # Test getting preferences
        prefs = db_manager.get_user_preferences(chat_id)
        assert prefs is not None
        assert prefs[0] == 'en'
        assert prefs[1] == 'es'
        assert prefs[2] == 'translation'  # default mode

    def test_user_stats_operations(self, db_session):
        """Test user statistics operations"""
        from src.models.database import DatabaseManager

        db_manager = DatabaseManager()
        user_id = 67890

        # Test initial stats (should be None)
        initial_stats = db_manager.get_user_stats(user_id)
        assert initial_stats is None

        # Test updating stats
        success = db_manager.update_user_stats(user_id)
        assert success

        # Test getting stats after update
        stats = db_manager.get_user_stats(user_id)
        assert stats is not None
        assert stats['translations'] == 1
        assert 'joined' in stats
        assert 'last_activity' in stats

    def test_chat_mode_operations(self, db_session):
        """Test chat mode operations"""
        from src.models.database import DatabaseManager

        db_manager = DatabaseManager()
        chat_id = 54321

        # Test default chat mode
        mode = db_manager.get_chat_mode(chat_id)
        assert mode == 'translation'

        # Test setting chat mode
        success = db_manager.set_chat_mode(chat_id, 'chat')
        assert success

        # Test getting updated chat mode
        mode = db_manager.get_chat_mode(chat_id)
        assert mode == 'chat'

    def test_message_translation_operations(self, db_session):
        """Test message translation storage and retrieval"""
        from src.models.database import DatabaseManager

        db_manager = DatabaseManager()

        chat_id = 11111
        message_id = 22222
        user_id = 33333
        original_text = "Hello world"
        translated_text = "Hola mundo"
        source_lang = "en"
        target_lang = "es"

        # Test storing translation
        success = db_manager.store_message_translation(
            chat_id, message_id, user_id, original_text,
            translated_text, source_lang, target_lang
        )
        assert success

        # Test retrieving translation
        translation = db_manager.get_message_translation(chat_id, message_id)
        assert translation is not None
        assert translation['original_text'] == original_text
        assert translation['translated_text'] == translated_text
        assert translation['source_language'] == source_lang
        assert translation['target_language'] == target_lang
        assert translation['user_id'] == user_id

    def test_language_selection_state_operations(self, db_session):
        """Test language selection state operations"""
        from src.models.database import DatabaseManager

        db_manager = DatabaseManager()
        chat_id = 99999

        # Test setting selection state
        success = db_manager.set_language_selection_state(chat_id, 'first_lang', 'en')
        assert success

        # Test getting selection state
        state = db_manager.get_language_selection_state(chat_id)
        assert state is not None
        assert state['step'] == 'first_lang'
        assert state['first_lang'] == 'en'

        # Test clearing selection state
        success = db_manager.clear_language_selection_state(chat_id)
        assert success

        # Test that state is cleared
        state = db_manager.get_language_selection_state(chat_id)
        assert state is None
