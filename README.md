# Telegram Language Buddy Bot

A smart translation bot that provides instant language conversion using Google Translate. Supports 40+ languages with persistent user preferences and database storage.

## 🌟 Features

- **Multi-language Support**: 40+ languages including Hebrew, Russian, Chinese, Arabic, and more
- **Smart Language Detection**: Automatically detects input language
- **Voice Message Transcription**: Transcribe and translate voice messages with multiple free model fallbacks
- **Persistent Preferences**: User language pairs are saved in database
- **Interactive Setup**: Easy `/setpair` command for language configuration
- **Statistics Tracking**: Monitor translation usage and user activity
- **Database Persistence**: SQLite for local development, PostgreSQL for production
- **Webhook Support**: Handles Telegram webhooks for real-time messaging
- **REST API**: Additional endpoints for manual translation and statistics

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
   set FLASK_ENV=development
   set PORT=5000
   ```
   
       **Optional**: For voice message transcription, add API keys:
    ```cmd
    set ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
    set GOOGLE_APPLICATION_CREDENTIALS=path/to/your/google-credentials.json
    ```

5. **Run the bot**
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
   export FLASK_ENV=development
   export PORT=5000
   ```
   
       **Optional**: For voice message transcription, add API keys:
    ```bash
    export ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
    export GOOGLE_APPLICATION_CREDENTIALS=path/to/your/google-credentials.json
    ```

5. **Run the bot**
   ```bash
   python -m src.main
   ```
   
   **Note**: The bot must be run as a module (`python -m src.main`) because it uses relative imports. Running it directly as a script (`python src/main.py`) will cause import errors.

### Environment Variables

Create a `.env` file in the project root (you can copy from `.env.example` as a template):

```env
# Required variables
TELEGRAM_BOT_TOKEN=your_bot_token_here
FLASK_ENV=development
DATABASE_URL=sqlite:///bot_data.db
SONAR_TOKEN=your_sonarqube_token_here
PORT=5000

# Optional: Voice transcription API keys
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/google-credentials.json
```

Or set them directly in your shell:

**Windows:**
```cmd
set TELEGRAM_BOT_TOKEN=your_bot_token_here
set FLASK_ENV=development
set PORT=5000
```

**Linux/macOS:**
```bash
export TELEGRAM_BOT_TOKEN=your_bot_token_here
export FLASK_ENV=development
export PORT=5000
```

**Required Environment Variables:**
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token from @BotFather
- `FLASK_ENV` - Set to 'development' for local work, 'production' for Heroku
- `DATABASE_URL` - Database connection string (auto-configured)
- `PORT` - Server port (auto-configured by Heroku)
- `SONAR_TOKEN` - SonarQube authentication token for code quality analysis

**Optional Voice Transcription API Keys:**
- `ASSEMBLYAI_API_KEY` - AssemblyAI API key for voice transcription (recommended)
- `GOOGLE_APPLICATION_CREDENTIALS` - Google Cloud credentials for Speech-to-Text

## 🔧 Database

The bot uses SQLAlchemy with automatic database selection:

### Local Development

For local development, the bot automatically uses SQLite:

```bash
# Database is automatically initialized when you run the bot
python -m src.main
```

The SQLite database file (`bot_data.db`) will be created in the project root.

### Heroku Deployment

The bot automatically uses PostgreSQL on Heroku:

- **Database**: PostgreSQL (Essential 0 plan, ~$5/month)
- **Persistence**: Data persists across deployments
- **Automatic Setup**: Database tables are created automatically
- **Schema Management**: Automatic PostgreSQL schema fixes for chat_id columns

**To view database logs:**
```bash
heroku logs --tail
```

## 📱 Bot Commands

- `/start` - Welcome message and instructions
- `/setpair` - Set your preferred language pair (two-step process)
- `/stats` - View translation statistics
- `/help` - Show available commands
- `/languages` - List all supported languages

## 🎤 Voice Message Support

The bot now supports voice message transcription and translation! Simply send a voice message and the bot will:

1. **Transcribe** the voice message using free AI models
2. **Detect** the language automatically
3. **Translate** to your target language (if configured)
4. **Display** both transcription and translation

### Voice Transcription Features

- **Multiple Free Models**: Uses fallback system with multiple free transcription services
- **Automatic Language Detection**: Detects spoken language automatically
- **Rate Limiting**: Respects API rate limits to avoid service disruptions
- **Error Handling**: Graceful fallback when services are unavailable
- **Quality Feedback**: Provides helpful error messages when transcription fails

### Supported Voice Transcription Services

1. **AssemblyAI** (Primary) - High accuracy, excellent language detection
2. **Google Speech-to-Text** (Primary) - Enterprise-grade transcription

### Setting Up Voice Transcription

To enable voice transcription, add one or more API keys to your environment:

```env
# Primary services (recommended)
ASSEMBLYAI_API_KEY=your_assemblyai_api_key
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/google-credentials.json
```

**Note**: Voice transcription works even without API keys, but will show an error message when users send voice messages.

### Voice Message Workflow

1. **User sends voice message** → Bot shows "Processing..." message
2. **Bot downloads audio** → Downloads from Telegram servers
3. **Bot transcribes audio** → Uses available transcription services
4. **Bot detects language** → Automatically detects spoken language
5. **Bot translates** → Translates to user's target language (if configured)
6. **Bot responds** → Shows transcription and translation

### Error Handling

If all transcription services fail, the bot will:
- Show a helpful error message
- Explain possible reasons for failure
- Suggest trying a text message instead
- Continue working normally for text messages

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
│   │   ├── voice_transcriber.py # Voice message transcription
│   │   └── telegram_bot.py      # Main bot logic
│   └── main.py                  # Flask application entry point
├── tests/
│   └── test_voice_transcriber.py # Voice transcription tests
├── requirements.txt             # Python dependencies
├── Procfile                     # Heroku deployment configuration
└── README.md                    # This file
```

## 🌐 API Endpoints

The bot provides several REST API endpoints:

- `GET /` - Health check and service status
- `POST /webhook` - Telegram webhook handler
- `POST /set_webhook` - Set Telegram webhook URL
- `POST /translate` - Manual translation endpoint
- `GET /stats` - Get bot statistics
- `GET /voice-status` - Get voice transcription service status

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
   heroku config:set FLASK_ENV=production
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

3. **Database connection errors**
   ```bash
   # Database is automatically initialized when the bot starts
   python -m src.main
   ```

4. **Language detection not working**
   - Check if the language is supported in `src/models/language_detector.py`
   - Verify the language code mapping in `src/models/free_translator.py`

5. **Heroku deployment fails**
   ```bash
   heroku logs --tail
   ```

6. **Database connection issues**
   - Check if PostgreSQL addon is active: `heroku addons`
   - Verify DATABASE_URL is set: `heroku config`
   - View database logs: `heroku logs --tail`

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
