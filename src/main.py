import os
import logging
from flask import Flask

from .controllers import home, webhook, set_webhook, manual_translate, get_stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Register routes
app.route('/')(home)
app.route('/webhook', methods=['POST'])(webhook)
app.route('/set_webhook', methods=['POST'])(set_webhook)
app.route('/translate', methods=['POST'])(manual_translate)
app.route('/stats')(get_stats)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)