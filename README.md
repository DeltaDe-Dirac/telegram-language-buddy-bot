# Telegram Language Buddy Bot

A comprehensive multilingual translation bot that provides instant text and voice message translation using Google Translate and multiple AI transcription services. Features persistent user preferences, intelligent fallback systems, and supports 40+ languages with full database persistence.

## 🌟 Features

- **Multi-language Support**: 40+ languages including Hebrew, Russian, Chinese, Arabic, Thai, and more
- **Smart Language Detection**: Automatically detects input language using multiple detection methods
- **Advanced Voice Transcription**: Multi-service transcription with intelligent fallback (Whisper, AssemblyAI, Google Speech-to-Text)
- **Persistent Preferences**: User language pairs saved in database with automatic schema management
- **Interactive Setup**: Two-step language pair configuration with inline keyboards
- **Statistics Tracking**: Comprehensive usage analytics and user activity monitoring
- **Database Persistence**: SQLite for local development, PostgreSQL for production with automatic migrations
- **Webhook Support**: Robust Telegram webhook handling with error recovery
- **REST API**: Complete REST API with health checks, manual translation, and service status endpoints
- **Quality Assurance**: SonarQube integration, comprehensive test suite with pytest and coverage reporting
- **Deployment Ready**: Multiple deployment configurations for Railway, Render, Fly.io, and Heroku

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
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
FLASK_ENV=development
PORT=5000
DATABASE_URL=sqlite:///bot_data.db

# Voice Transcription API Keys (at least one required for voice features)
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
GOOGLE_APPLICATION_CREDENTIALS_JSON=your_google_credentials_json_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Legacy/premium translation services
HUGGINGFACE_API_TOKEN=your_huggingface_api_token_here

# Quality assurance and development
SONAR_TOKEN=your_sonarqube_token_here
SONAR_TOKEN_VS_CODE=your_sonarqube_vs_code_token_here
RAILWAY_TOKEN=your_railway_token_here
```

Or set them directly in your shell:

**Windows:**
```cmd
set TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
set FLASK_ENV=development
set PORT=5000
set DATABASE_URL=sqlite:///bot_data.db
set OPENAI_API_KEY=your_openai_api_key_here
set ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
```

**Linux/macOS:**
```bash
export TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
export FLASK_ENV=development
export PORT=5000
export DATABASE_URL=sqlite:///bot_data.db
export OPENAI_API_KEY=your_openai_api_key_here
export ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
```

**Required Environment Variables:**
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token from @BotFather
- `FLASK_ENV` - Set to 'development' for local work, 'production' for deployment
- `PORT` - Server port (default: 5000, auto-configured by deployment platforms)
- `DATABASE_URL` - Database connection string (SQLite for local, PostgreSQL for production)

**Voice Transcription API Keys (at least one required):**
- `OPENAI_API_KEY` - OpenAI API key for Whisper transcription (recommended primary)
- `ASSEMBLYAI_API_KEY` - AssemblyAI API key for high-accuracy transcription
- `GOOGLE_APPLICATION_CREDENTIALS_JSON` - Google Cloud Speech-to-Text credentials

**Optional Environment Variables:**
- `HUGGINGFACE_API_TOKEN` - Hugging Face API token for premium translations (legacy)
- `SONAR_TOKEN` - SonarQube token for code quality analysis
- `SONAR_TOKEN_VS_CODE` - VS Code SonarQube extension token
- `RAILWAY_TOKEN` - Railway CLI token for MCP server integration

## 🔧 Database

The bot uses SQLAlchemy with automatic database selection:

### Local Development

For local development, the bot automatically uses SQLite:

```bash
# Database is automatically initialized when you run the bot
python -m src.main
```

The SQLite database file (`bot_data.db`) will be created in the project root.

### Production Deployment (Railway/Render/Heroku)

The bot automatically uses PostgreSQL in production:

- **Database**: PostgreSQL (free tier available on Railway/Render)
- **Persistence**: Data persists across deployments
- **Automatic Setup**: Database tables are created automatically
- **Schema Management**: Automatic PostgreSQL schema fixes for chat_id columns

**Database Configuration:**
- Railway: Automatically provisions PostgreSQL and sets `DATABASE_URL`
- Render: Add PostgreSQL service, automatically linked via `DATABASE_URL`
- Heroku: Add PostgreSQL addon, automatically sets `DATABASE_URL`

**To view logs:**
- Railway: `railway logs` (or use Railway dashboard)
- Render: View logs in Render dashboard
- Heroku: `heroku logs --tail`

## 📱 Bot Commands

- `/start` - Welcome message and instructions
- `/setpair` - Set your preferred language pair (two-step process)
- `/stats` - View translation statistics
- `/chatmode` - Toggle translation mode (enable/disable translations)
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

1. **Whisper (OpenAI)** (Primary) - State-of-the-art transcription with excellent accuracy
2. **AssemblyAI** (Primary) - High accuracy, excellent language detection
3. **Google Speech-to-Text** (Primary) - Enterprise-grade transcription with broad language support

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
│   │   └── bot_controller.py      # Flask routes and webhook handling
│   ├── models/
│   │   ├── database.py            # Database models and manager
│   │   ├── free_translator.py     # Google Translate integration
│   │   ├── language_detector.py   # Language detection utilities
│   │   ├── telegram_bot.py        # Main Telegram bot logic
│   │   ├── transcription_result.py # Transcription result data models
│   │   ├── voice_transcriber.py   # Multi-service voice transcription
│   │   └── whisper_transcriber.py # OpenAI Whisper integration
│   └── main.py                    # Flask application entry point
├── tests/
│   ├── conftest.py                # Pytest configuration and fixtures
│   ├── fixtures/                  # Test audio files and fixtures
│   │   ├── russian_voice.mp3/.ogg
│   │   └── thai_voice.mp3/.ogg
│   ├── mock_googletrans.py        # Google Translate mocking utilities
│   ├── test_*.py                  # Comprehensive test suite
│   └── README.md                  # Test documentation
├── scripts/
│   ├── generate_russian_tts.py    # Russian TTS generation for testing
│   ├── generate_thai_tts.py       # Thai TTS generation for testing
│   └── run_integration.py         # Integration test runner
├── sonar-scanner-5.0.1.3006-windows/  # SonarQube scanner
├── requirements.txt               # Python dependencies
├── pytest.ini                     # Pytest configuration
├── sonar-project.properties       # SonarQube configuration
├── railway.json                   # Railway deployment config
├── render.yaml                    # Render deployment config
├── Procfile                       # Heroku deployment config
├── .env.example                   # Environment variables template
└── README.md                      # This file
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

> 💡 **Want to deploy for FREE?** Check out [FREE_DEPLOYMENT.md](FREE_DEPLOYMENT.md) for detailed guides on Railway, Render, and Fly.io!

### Railway Deployment (Free Tier Available) ⭐ Recommended

Railway offers a free tier with $5/month credit, perfect for small bots!

1. **Sign up at [Railway](https://railway.app/)**
   - Use GitHub to sign in for easy deployment

2. **Create a new project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose this repository

3. **Add PostgreSQL database**
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway automatically sets `DATABASE_URL` environment variable

4. **Set environment variables**
   - Go to your service → "Variables"
   - Add:
     - `TELEGRAM_BOT_TOKEN=your_bot_token_here`
     - `FLASK_ENV=production`
     - `OPENAI_API_KEY=your_openai_api_key_here` (for Whisper transcription)
   - Optional additional voice transcription keys:
     - `ASSEMBLYAI_API_KEY=your_assemblyai_key_here`
     - `GOOGLE_APPLICATION_CREDENTIALS_JSON=your_google_credentials_json_here`

5. **Deploy**
   - Railway automatically deploys on every push to main
   - Or click "Deploy" to deploy manually

6. **Set Telegram webhook**
   - Get your Railway URL from the service settings
   - Set webhook:
     ```bash
     curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
          -H "Content-Type: application/json" \
          -d '{"url": "https://your-app.railway.app/webhook"}'
     ```

**Cost**: Free tier includes $5/month credit (usually enough for small bots)

### Render Deployment (Free Tier Available)

Render offers a free tier with some limitations (spins down after inactivity).

1. **Sign up at [Render](https://render.com/)**
   - Use GitHub to sign in

2. **Create a new Web Service**
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Select this repository

3. **Configure the service**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn src.main:app`
   - **Environment**: `Python 3`

4. **Add PostgreSQL database**
   - Click "New" → "PostgreSQL"
   - Select "Free" plan
   - Render automatically sets `DATABASE_URL` in your web service

5. **Set environment variables**
   - In your web service settings → "Environment"
   - Add:
     - `FLASK_ENV=production`
     - `TELEGRAM_BOT_TOKEN=your_bot_token_here`
   - Optional voice transcription keys

6. **Deploy**
   - Render automatically deploys on every push
   - First deployment may take a few minutes

7. **Set Telegram webhook**
   - Get your Render URL (e.g., `your-app.onrender.com`)
   - Set webhook:
     ```bash
     curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
          -H "Content-Type: application/json" \
          -d '{"url": "https://your-app.onrender.com/webhook"}'
     ```

**Note**: Free tier services spin down after 15 minutes of inactivity. First request may take ~30 seconds to wake up.

**Cost**: Free tier available (with limitations)

### Heroku Deployment (Paid)

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

## 🧪 Testing & Quality Assurance

### Test Suite

The project includes a comprehensive test suite with multiple testing frameworks:

```bash
# Run all tests
pytest

# Run integration tests only
pytest -m integration

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_voice_transcriber.py
```

### Test Categories

- **Unit Tests**: Core functionality testing
- **Integration Tests**: End-to-end voice transcription workflows
- **Database Tests**: Data persistence and schema validation
- **API Tests**: REST endpoint validation

### Quality Assurance Tools

#### SonarQube Integration

The project includes SonarQube configuration for code quality analysis:

```bash
# Run SonarQube analysis
sonar-scanner
```

Configuration includes:
- Code coverage reporting
- Security vulnerability scanning
- Code smell detection
- Maintainability metrics

#### Test Fixtures

Test audio files are provided for voice transcription testing:
- `tests/fixtures/russian_voice.mp3/.ogg` - Russian language samples
- `tests/fixtures/thai_voice.mp3/.ogg` - Thai language samples

### Scripts

Utility scripts for development and testing:

```bash
# Generate test audio files
python scripts/generate_russian_tts.py
python scripts/generate_thai_tts.py

# Run integration tests
python scripts/run_integration.py
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

5. **Voice transcription not working**
   - Verify API keys are set: `ASSEMBLYAI_API_KEY` or `OPENAI_API_KEY`
   - Check service availability in logs for debug messages

6. **Heroku deployment fails**
   ```bash
   heroku logs --tail
   ```

7. **Database connection issues**
   - Check if PostgreSQL addon is active: `heroku addons`
   - Verify DATABASE_URL is set: `heroku config`
   - View database logs: `heroku logs --tail`

### Debug Mode

Enable debug logging by setting the log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Production Debugging

For production issues, check Railway/Render logs or enable additional debug logging:

```python
# In production, logs show service availability
[DEBUG] OPENAI_API_KEY raw exists: True
[DEBUG] Whisper available: True
[DEBUG] whisper_transcriber.available: True
Voice transcription services available: {'whisper': True, 'assemblyai': True, 'google_speech': False}
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
