import os
import logging
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, DateTime, Text, text
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

Base = declarative_base()

class UserPreferences(Base):
    """Database model for user language preferences"""
    __tablename__ = 'user_preferences'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True, nullable=False)
    language1 = Column(String(10), nullable=False)
    language2 = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class UserStats(Base):
    """Database model for user statistics"""
    __tablename__ = 'user_stats'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    translations = Column(Integer, default=0)
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_activity = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class LanguageSelectionState(Base):
    """Database model for language selection state during two-step process"""
    __tablename__ = 'language_selection_state'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True, nullable=False)
    step = Column(String(20), nullable=False)  # 'first_lang' or 'second_lang'
    first_lang = Column(String(10), nullable=True)  # Only set when step is 'second_lang'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class MessageTranslation(Base):
    """Database model for storing message translations to handle edits"""
    __tablename__ = 'message_translations'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    message_id = Column(Integer, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Composite unique constraint to prevent duplicates
    __table_args__ = (
        {'sqlite_autoincrement': True} if 'sqlite' in os.getenv('DATABASE_URL', 'sqlite:///bot_data.db') else {}
    )

class DatabaseManager:
    """Database manager for the bot"""
    
    # Class attributes for testing
    engine = None
    session_local = None
    
    def __init__(self):
        # Use SQLite for simplicity, can be changed to PostgreSQL for production
        database_url = os.getenv('DATABASE_URL', 'sqlite:///bot_data.db')
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        self.engine = create_engine(database_url)
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Set class attributes for testing
        DatabaseManager.engine = self.engine
        DatabaseManager.session_local = self.session_local
        
        # Create tables
        self._ensure_proper_schema()
        logger.info("Database initialized")
    
    def _ensure_proper_schema(self):
        """Ensure database schema has proper column types for chat_id"""
        try:
            # Check if we're using PostgreSQL
            if 'postgresql' in str(self.engine.url):
                logger.info("Detected PostgreSQL database, ensuring proper schema...")
                self._fix_postgresql_schema()
            else:
                # For SQLite, just create tables normally
                Base.metadata.create_all(bind=self.engine)
        except (OSError, ImportError, AttributeError) as e:
            logger.error(f"Error ensuring proper schema: {e}")
            # Fallback to normal table creation
            Base.metadata.create_all(bind=self.engine)
    
    def _fix_postgresql_schema(self):
        """Fix PostgreSQL schema to use BIGINT for chat_id and user_id columns"""
        try:
            with self.engine.connect() as conn:
                # Check if tables exist
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('user_preferences', 'language_selection_state', 'message_translations', 'user_stats')
                """))
                existing_tables = [row[0] for row in result]
                
                if not existing_tables:
                    # No tables exist, create them normally
                    Base.metadata.create_all(bind=self.engine)
                    logger.info("Created new tables with proper schema")
                    return
                
                # Check columns that need to be BIGINT and drop tables that need fixing
                tables_to_recreate = set()
                
                for table_name in existing_tables:
                    # Check chat_id column for tables that have it
                    if table_name in ['user_preferences', 'language_selection_state', 'message_translations']:
                        result = conn.execute(text(f"""
                            SELECT data_type 
                            FROM information_schema.columns 
                            WHERE table_name = '{table_name}' 
                            AND column_name = 'chat_id'
                        """))
                        column_type = result.fetchone()
                        
                        if column_type and column_type[0] != 'bigint':
                            logger.warning(f"Table {table_name} has chat_id as {column_type[0]}, need to fix...")
                            tables_to_recreate.add(table_name)
                    
                    # Check user_id column for tables that have it
                    if table_name in ['user_stats', 'message_translations']:
                        result = conn.execute(text(f"""
                            SELECT data_type 
                            FROM information_schema.columns 
                            WHERE table_name = '{table_name}' 
                            AND column_name = 'user_id'
                        """))
                        column_type = result.fetchone()
                        
                        if column_type and column_type[0] != 'bigint':
                            logger.warning(f"Table {table_name} has user_id as {column_type[0]}, need to fix...")
                            tables_to_recreate.add(table_name)
                
                # Drop tables that need to be recreated
                for table_name in tables_to_recreate:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                    logger.info(f"Dropped table {table_name} to recreate with proper schema")
                
                # Create tables with proper schema
                Base.metadata.create_all(bind=self.engine)
                logger.info("Recreated tables with proper BIGINT chat_id and user_id columns")
                
        except (OSError, ImportError, AttributeError, ValueError) as e:
            logger.error(f"Error fixing PostgreSQL schema: {e}")
            # Fallback to normal table creation
            Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.session_local()
    
    @classmethod
    def get_session_class(cls):
        """Get database session (class method for testing)"""
        if cls.session_local is None:
            raise RuntimeError("DatabaseManager not initialized")
        return cls.session_local()
    
    def get_user_preferences(self, chat_id: int) -> tuple[str, str] | None:
        """Get language preferences for a chat"""
        with self.get_session() as session:
            try:
                prefs = session.query(UserPreferences).filter(UserPreferences.chat_id == chat_id).first()
                if prefs:
                    return (prefs.language1, prefs.language2)
                return None
            except (OSError, ImportError, AttributeError, ValueError) as e:
                logger.error(f"Error getting preferences for chat {chat_id}: {e}")
                return None
    
    def set_user_preferences(self, chat_id: int, lang1: str, lang2: str) -> bool:
        """Set language preferences for a chat"""
        with self.get_session() as session:
            try:
                # Check if preferences already exist
                existing = session.query(UserPreferences).filter(UserPreferences.chat_id == chat_id).first()
                
                if existing:
                    # Update existing preferences
                    existing.language1 = lang1.lower()
                    existing.language2 = lang2.lower()
                    existing.updated_at = datetime.now(timezone.utc)
                else:
                    # Create new preferences
                    new_prefs = UserPreferences(
                        chat_id=chat_id,
                        language1=lang1.lower(),
                        language2=lang2.lower()
                    )
                    session.add(new_prefs)
                
                session.commit()
                logger.info(f"Saved preferences for chat {chat_id}: {lang1} ↔ {lang2}")
                return True
                
            except (OSError, ImportError, AttributeError, ValueError) as e:
                session.rollback()
                logger.error(f"Error saving preferences for chat {chat_id}: {e}")
                return False
    
    def get_user_stats(self, user_id: int) -> dict | None:
        """Get user statistics"""
        with self.get_session() as session:
            try:
                stats = session.query(UserStats).filter(UserStats.user_id == user_id).first()
                if stats:
                    return {
                        'translations': stats.translations,
                        'joined': stats.joined_at,
                        'last_activity': stats.last_activity
                    }
                return None
            except (OSError, ImportError, AttributeError, ValueError) as e:
                logger.error(f"Error getting stats for user {user_id}: {e}")
                return None
    
    def update_user_stats(self, user_id: int) -> bool:
        """Update user translation statistics"""
        with self.get_session() as session:
            try:
                stats = session.query(UserStats).filter(UserStats.user_id == user_id).first()
                
                if stats:
                    # Update existing stats
                    stats.translations += 1
                    stats.last_activity = datetime.now(timezone.utc)
                else:
                    # Create new stats
                    new_stats = UserStats(
                        user_id=user_id,
                        translations=1
                    )
                    session.add(new_stats)
                
                session.commit()
                return True
                
            except (OSError, ImportError, AttributeError, ValueError) as e:
                session.rollback()
                logger.error(f"Error updating stats for user {user_id}: {e}")
                return False
    
    def get_all_preferences(self) -> dict:
        """Get all user preferences (for debugging)"""
        with self.get_session() as session:
            try:
                prefs = session.query(UserPreferences).all()
                return {p.chat_id: (p.language1, p.language2) for p in prefs}
            except (OSError, ImportError, AttributeError, ValueError) as e:
                logger.error(f"Error getting all preferences: {e}")
                return {}
    
    def get_language_selection_state(self, chat_id: int) -> dict | None:
        """Get language selection state for a chat"""
        with self.get_session() as session:
            try:
                state = session.query(LanguageSelectionState).filter(LanguageSelectionState.chat_id == chat_id).first()
                if state:
                    return {
                        'step': state.step,
                        'first_lang': state.first_lang
                    }
                return None
            except (OSError, ImportError, AttributeError, ValueError) as e:
                logger.error(f"Error getting selection state for chat {chat_id}: {e}")
                return None
    
    def set_language_selection_state(self, chat_id: int, step: str, first_lang: str = None) -> bool:
        """Set language selection state for a chat"""
        with self.get_session() as session:
            try:
                # Check if state already exists
                existing = session.query(LanguageSelectionState).filter(LanguageSelectionState.chat_id == chat_id).first()
                
                if existing:
                    # Update existing state
                    existing.step = step
                    existing.first_lang = first_lang
                    existing.updated_at = datetime.now(timezone.utc)
                else:
                    # Create new state
                    new_state = LanguageSelectionState(
                        chat_id=chat_id,
                        step=step,
                        first_lang=first_lang
                    )
                    session.add(new_state)
                
                session.commit()
                logger.info(f"Saved selection state for chat {chat_id}: step={step}, first_lang={first_lang}")
                return True
                
            except (OSError, ImportError, AttributeError, ValueError) as e:
                session.rollback()
                logger.error(f"Error saving selection state for chat {chat_id}: {e}")
                return False
    
    def clear_language_selection_state(self, chat_id: int) -> bool:
        """Clear language selection state for a chat"""
        with self.get_session() as session:
            try:
                state = session.query(LanguageSelectionState).filter(LanguageSelectionState.chat_id == chat_id).first()
                if state:
                    session.delete(state)
                    session.commit()
                    logger.info(f"Cleared selection state for chat {chat_id}")
                return True
            except (OSError, ImportError, AttributeError, ValueError) as e:
                session.rollback()
                logger.error(f"Error clearing selection state for chat {chat_id}: {e}")
                return False
    
    def store_message_translation(self, chat_id: int, message_id: int, user_id: int, 
                                 original_text: str, translated_text: str, 
                                 source_language: str, target_language: str) -> bool:
        """Store a message translation for later retrieval on edit"""
        with self.get_session() as session:
            try:
                # Check if translation already exists for this message
                existing = session.query(MessageTranslation).filter(
                    MessageTranslation.chat_id == chat_id,
                    MessageTranslation.message_id == message_id
                ).first()
                
                if existing:
                    # Update existing translation
                    existing.original_text = original_text
                    existing.translated_text = translated_text
                    existing.source_language = source_language
                    existing.target_language = target_language
                else:
                    # Create new translation record
                    new_translation = MessageTranslation(
                        chat_id=chat_id,
                        message_id=message_id,
                        user_id=user_id,
                        original_text=original_text,
                        translated_text=translated_text,
                        source_language=source_language,
                        target_language=target_language
                    )
                    session.add(new_translation)
                
                session.commit()
                logger.info(f"Stored translation for message {message_id} in chat {chat_id}")
                return True
                
            except (OSError, ImportError, AttributeError, ValueError) as e:
                session.rollback()
                logger.error(f"Error storing translation for message {message_id} in chat {chat_id}: {e}")
                return False
    
    def get_message_translation(self, chat_id: int, message_id: int) -> dict | None:
        """Get stored translation for a specific message"""
        with self.get_session() as session:
            try:
                translation = session.query(MessageTranslation).filter(
                    MessageTranslation.chat_id == chat_id,
                    MessageTranslation.message_id == message_id
                ).first()
                
                if translation:
                    return {
                        'original_text': translation.original_text,
                        'translated_text': translation.translated_text,
                        'source_language': translation.source_language,
                        'target_language': translation.target_language,
                        'user_id': translation.user_id,
                        'created_at': translation.created_at
                    }
                return None
                
            except (OSError, ImportError, AttributeError, ValueError) as e:
                logger.error(f"Error getting translation for message {message_id} in chat {chat_id}: {e}")
                return None