# Telegram Language Buddy Bot

A smart translation bot that provides instant language conversion using Google Translate. Supports 40+ languages with persistent user preferences and database storage.

## 🌟 Features

- **Multi-language Support**: 40+ languages including Hebrew, Russian, Chinese, Arabic, and more
- **Smart Language Detection**: Automatically detects input language
- **Persistent Preferences**: User language pairs are saved in database
- **Interactive Setup**: Easy `/setpair` command for language configuration
- **Statistics Tracking**: Monitor translation usage and user activity
- **Database Persistence**: SQLite for local development, PostgreSQL for production

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Telegram Bot Token (get from [@BotFather](https://t.me/botfather))
- Git

### Installation

#### Windows

1. **Clone the repository**
   ```cmd
   git clone https://github.com/DeltaDe-Dirac/telegram-language-buddy-bot.git
   cd telegram-language-buddy-bot
   ```

2. **Create virtual environment**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```cmd
   set TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

5. **Initialize database**
   ```cmd
   python init_db.py
   ```

6. **Run the bot**
   ```cmd
   python -m src.main
   ```
   
   **Note**: The bot must be run as a module (`python -m src.main`) because it uses relative imports. Running it directly as a script (`python src/main.py`) will cause import errors.

#### Linux/macOS

1. **Clone the repository**
   ```bash
   git clone https://github.com/DeltaDe-Dirac/telegram-language-buddy-bot.git
   cd telegram-language-buddy-bot
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   export TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

5. **Initialize database**
   ```bash
   python init_db.py
   ```

6. **Run the bot**
   ```bash
   python -m src.main
   ```
   
   **Note**: The bot must be run as a module (`python -m src.main`) because it uses relative imports. Running it directly as a script (`python src/main.py`) will cause import errors.

### Environment Variables

Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_URL=sqlite:///bot_data.db
```

Or set them directly in your shell:

**Windows:**
```cmd
set TELEGRAM_BOT_TOKEN=your_bot_token_here
```

**Linux/macOS:**
```bash
export TELEGRAM_BOT_TOKEN=your_bot_token_here
```

## 🔧 Database Management

The bot includes a comprehensive database backup/restore system for local development:

### Local Development

```bash
# List available backups
python manage_db.py list

# Create backup
python manage_db.py backup

# Restore from most recent backup
python manage_db.py restore

# Restore from specific backup
python manage_db.py restore 2
```

### Heroku Deployment

**Important**: Database management scripts (`manage_db.py`, `backup_db.py`) are for local development only. Heroku uses an ephemeral filesystem, so these scripts won't work on Heroku.

For Heroku, the bot automatically handles database persistence:

1. **Automatic Backup/Restore**: The `Procfile` runs `restore_db.py && init_db.py` on each deployment
2. **Database Persistence**: Uses SQLite locally, can be upgraded to PostgreSQL on Heroku

**To upgrade to PostgreSQL on Heroku:**

```bash
# Add PostgreSQL addon
heroku addons:create heroku-postgresql:mini

# The bot will automatically use DATABASE_URL from Heroku
```

**To view Heroku database logs:**
```bash
heroku logs --tail
```

**Current Limitation**: The current setup uses SQLite on Heroku, which gets wiped on each deployment. For production use, consider upgrading to PostgreSQL:

```bash
# Add PostgreSQL (recommended for production)
heroku addons:create heroku-postgresql:mini

# The bot will automatically detect and use PostgreSQL
```

## 📱 Bot Commands

- `/start` - Welcome message and instructions
- `/setpair` - Set your preferred language pair
- `/stats` - View translation statistics
- `/help` - Show available commands

## 🌐 Supported Languages

The bot supports 40+ languages including:

- **European**: English, Spanish, French, German, Italian, Portuguese, Russian, Polish, Dutch, Swedish, Danish, Norwegian, Finnish, Greek, Ukrainian, Czech, Slovak, Hungarian, Romanian, Bulgarian, Croatian, Serbian, Slovenian, Estonian, Latvian, Lithuanian

- **Asian**: Chinese, Japanese, Korean, Thai, Vietnamese, Indonesian, Malay, Filipino, Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Sinhala

- **Middle Eastern**: Arabic, Hebrew, Persian, Turkish, Urdu

## 🏗️ Project Structure

```
telegram-language-buddy-bot/
├── src/
│   ├── controllers/
│   │   └── bot_controller.py    # Flask routes and webhook handling
│   ├── models/
│   │   ├── database.py          # Database models and manager
│   │   ├── free_translator.py   # Google Translate integration
│   │   ├── language_detector.py # Language detection utilities
│   │   └── telegram_bot.py      # Main bot logic
│   └── main.py                  # Flask application entry point
├── backup_db.py                 # Database backup script
├── restore_db.py                # Database restore script
├── manage_db.py                 # Database management interface
├── init_db.py                   # Database initialization
├── deploy.sh                    # Automated deployment script
├── requirements.txt             # Python dependencies
├── Procfile                     # Heroku deployment configuration
└── README.md                    # This file
```

## 🚀 Deployment

### Heroku Deployment

1. **Install Heroku CLI**
   ```bash
   # Windows
   winget install --id=Heroku.HerokuCLI
   
   # Linux
   curl https://cli-assets.heroku.com/install.sh | sh
   ```

2. **Login to Heroku**
   ```bash
   heroku login
   ```

3. **Create Heroku app**
   ```bash
   heroku create your-app-name
   ```

4. **Set environment variables**
   ```bash
   heroku config:set TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

5. **Deploy**
   ```bash
   git push heroku main
   ```

### Local Development with Webhook

For local development with webhooks, you can use ngrok:

1. **Install ngrok**
   ```bash
   # Download from https://ngrok.com/download
   ```

2. **Start ngrok tunnel**
   ```bash
   ngrok http 5000
   ```

3. **Set webhook URL**
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
        -H "Content-Type: application/json" \
        -d '{"url": "https://your-ngrok-url.ngrok.io/webhook"}'
   ```

## 🔍 Troubleshooting

### Common Issues

1. **Import errors when running the bot**
   ```bash
   # ❌ Wrong - will cause import errors
   python src/main.py
   
   # ✅ Correct - run as module
   python -m src.main
   ```

2. **"No module named 'googletrans'"**
   ```bash
   pip install googletrans==3.1.0a0
   ```

2. **Database connection errors**
   ```bash
   python init_db.py
   ```

3. **Language detection not working**
   - Check if the language is supported in `src/models/language_detector.py`
   - Verify the language code mapping in `src/models/free_translator.py`

4. **Heroku deployment fails**
   ```bash
   heroku logs --tail
   ```

5. **Database management scripts not working on Heroku**
   - These scripts are for local development only
   - Heroku uses ephemeral filesystem
   - Use `heroku logs --tail` to view database operations
   - Consider upgrading to PostgreSQL: `heroku addons:create heroku-postgresql:mini`

### Debug Mode

Enable debug logging by setting the log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Google Translate](https://translate.google.com/) for translation services
- [googletrans](https://github.com/ssut/py-googletrans) Python library
- [SQLAlchemy](https://www.sqlalchemy.org/) for database management
- [Flask](https://flask.palletsprojects.com/) web framework
