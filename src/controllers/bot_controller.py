import json
import logging
import requests
from datetime import datetime
from flask import request, jsonify

from ..models import LanguageDetector, TelegramBot

logger = logging.getLogger(__name__)

# Initialize the bot (will be created when needed)
bot = None

def get_bot():
    """Get or create bot instance"""
    global bot
    if bot is None:
        bot = TelegramBot()
    return bot

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
        
    except Exception as e:
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
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def manual_translate():
    """Manual translation endpoint for testing"""
    try:
        data = request.get_json()
        text = data.get('text')
        lang1 = data.get('lang1', get_bot().translator.detect_language(text))
        lang2 = data.get('lang2', 'en')
        
        translated = get_bot().translator.translate_text(text, lang2, lang1)
        
        return jsonify({
            "original": text,
            "translated": translated,
            "source_language": lang1,
            "target_language": lang2,
            "language_pair": f"{lang1} ↔ {lang2}"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_stats():
    """Get bot statistics"""
    try:
        total_users = len(get_bot().user_preferences)
        total_translations = sum(stats.get('translations', 0) for stats in get_bot().user_stats.values())
        
        language_distribution = {}
        for lang_pair in get_bot().user_preferences.values():
            # Count each language in the pair
            for lang in lang_pair:
                language_distribution[lang] = language_distribution.get(lang, 0) + 1
        
        return jsonify({
            "total_users": total_users,
            "total_translations": total_translations,
            "language_distribution": language_distribution,
            "supported_languages": len(LanguageDetector.SUPPORTED_LANGUAGES)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500 