import os
import logging
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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
    user_id = Column(Integer, unique=True, nullable=False)
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

class DatabaseManager:
    """Database manager for the bot"""
    
    def __init__(self):
        # Use SQLite for simplicity, can be changed to PostgreSQL for production
        database_url = os.getenv('DATABASE_URL', 'sqlite:///bot_data.db')
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        self.engine = create_engine(database_url)
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database initialized")
    
    def get_session(self):
        """Get database session"""
        return self.session_local()
    
    def get_user_preferences(self, chat_id: int) -> tuple[str, str] | None:
        """Get language preferences for a chat"""
        with self.get_session() as session:
            try:
                prefs = session.query(UserPreferences).filter(UserPreferences.chat_id == chat_id).first()
                if prefs:
                    return (prefs.language1, prefs.language2)
                return None
            except Exception as e:
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
                
            except Exception as e:
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
            except Exception as e:
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
                
            except Exception as e:
                session.rollback()
                logger.error(f"Error updating stats for user {user_id}: {e}")
                return False
    
    def get_all_preferences(self) -> dict:
        """Get all user preferences (for debugging)"""
        with self.get_session() as session:
            try:
                prefs = session.query(UserPreferences).all()
                return {p.chat_id: (p.language1, p.language2) for p in prefs}
            except Exception as e:
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
            except Exception as e:
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
                
            except Exception as e:
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
            except Exception as e:
                session.rollback()
                logger.error(f"Error clearing selection state for chat {chat_id}: {e}")
                return False