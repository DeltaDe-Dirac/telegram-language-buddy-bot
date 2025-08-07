import json
import logging
import requests
import threading
from datetime import datetime
from flask import request, jsonify

try:
    from models import LanguageDetector, TelegramBot
except ImportError:
    from ..models import LanguageDetector, TelegramBot

logger = logging.getLogger(__name__)

class BotSingleton:
    """Thread-safe singleton for TelegramBot instance"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._bot = None
        return cls._instance
    
    def get_bot(self):
        """Get or create bot instance"""
        if self._bot is None:
            with self._lock:
                if self._bot is None:
                    self._bot = TelegramBot()
                    logger.info("Created new TelegramBot instance")
        return self._bot

# Global singleton instance
bot_singleton = BotSingleton()

def get_bot():
    """Get bot instance from singleton"""
    return bot_singleton.get_bot()

def home():
    """Health check endpoint"""
    return {
        "status": "active",
        "service": "Telegram Language Buddy Bot",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

def webhook():
    """Handle Telegram webhook"""
    try:
        update = request.get_json()
        logger.info(f"Received update: {json.dumps(update, indent=2)}")
        
        get_bot().process_message(update)
        return jsonify({"ok": True})
        
    except (ValueError, TypeError, KeyError) as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

def set_webhook():
    """Set Telegram webhook URL"""
    try:
        webhook_url = request.json.get('url')
        if not webhook_url:
            return jsonify({"error": "URL is required"}), 400
        
        url = f"{get_bot().base_url}/setWebhook"
        payload = {"url": webhook_url}
        
        response = requests.post(url, json=payload)
        result = response.json()
        
        return jsonify(result)
        
    except (requests.RequestException, ValueError, KeyError) as e:
        return jsonify({"error": str(e)}), 500

def manual_translate():
    """Manual translation endpoint for testing"""
    try:
        data = request.get_json()
        text = data.get('text')
        detected_lang = get_bot().translator.detect_language(text)
        lang1 = data.get('lang1', detected_lang)
        lang2 = data.get('lang2', 'en')

        if detected_lang != lang1:
            logger.warning(f"Detected language is {detected_lang}, but requested to translate from {lang1}")
        
        translated = get_bot().translator.translate_text(text, lang2, lang1)
        
        return jsonify({
            "original": text,
            "translated": translated,
            "source_language": lang1,
            "target_language": lang2,
            "language_pair": f"{lang1} ↔ {lang2}"
        })
        
    except (ValueError, KeyError, TypeError) as e:
        return jsonify({"error": str(e)}), 500

def get_stats():
    """Get bot statistics from database"""
    try:
        bot = get_bot()
        all_preferences = bot.db.get_all_preferences()
        total_users = len(all_preferences)
        
        # Calculate total translations from database
        total_translations = 0
        language_distribution = {}
        
        # Get all user stats from database
        with bot.db.get_session() as session:
            from models.database import UserStats
            all_stats = session.query(UserStats).all()
            total_translations = sum(stats.translations for stats in all_stats)
        
        # Calculate language distribution
        for chat_id, lang_pair in all_preferences.items():
            # Count each language in the pair
            for lang in lang_pair:
                language_distribution[lang] = language_distribution.get(lang, 0) + 1
        
        return jsonify({
            "total_users": total_users,
            "total_translations": total_translations,
            "language_distribution": language_distribution,
            "supported_languages": len(LanguageDetector.SUPPORTED_LANGUAGES),
            "preferences_by_chat": {
                str(chat_id): lang_pair 
                for chat_id, lang_pair in all_preferences.items()
            },
            "storage_type": "database",
            "database_url": bot.db.engine.url
        })
        
    except (AttributeError, KeyError, TypeError) as e:
        return jsonify({"error": str(e)}), 500 