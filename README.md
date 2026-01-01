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
   - Optional voice transcription keys:
     - `ASSEMBLYAI_API_KEY=your_key`
     - `GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json`

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
