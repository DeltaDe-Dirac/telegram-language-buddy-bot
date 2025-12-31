# Free Deployment Guide

This guide helps you deploy the Telegram Language Buddy Bot to **free hosting platforms** to avoid monthly costs.

## 🎯 Platform Comparison

| Platform | Free Tier | Database | Sleep After Inactivity | Best For |
|----------|-----------|----------|------------------------|----------|
| **Railway** | $5/month credit | PostgreSQL included | No | ⭐ **Recommended** - Most reliable |
| **Render** | Free forever | PostgreSQL included | 15 min (wakes on request) | Good for low-traffic bots |
| **Fly.io** | Free tier | PostgreSQL available | No | Good alternative |

## 🚂 Railway Deployment (Recommended)

### Why Railway?
- ✅ $5/month free credit (usually enough for small bots)
- ✅ No sleep/wake delays
- ✅ Automatic PostgreSQL database
- ✅ Easy GitHub integration
- ✅ Simple environment variable management

### Step-by-Step Guide

1. **Sign Up**
   - Go to [railway.app](https://railway.app)
   - Sign in with GitHub

2. **Create Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `telegram-language-buddy-bot` repository
   - Railway will detect the `railway.json` configuration

3. **Add PostgreSQL Database**
   - In your project, click "New"
   - Select "Database" → "Add PostgreSQL"
   - Railway automatically:
     - Creates the database
     - Sets `DATABASE_URL` environment variable
     - Links it to your web service

4. **Configure Environment Variables**
   - Go to your web service → "Variables" tab
   - Add these required variables:
     ```
     TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
     FLASK_ENV=production
     ```
   - Optional (for voice transcription):
     ```
     ASSEMBLYAI_API_KEY=your_assemblyai_key
     GOOGLE_APPLICATION_CREDENTIALS=path/to/google-credentials.json
     ```

5. **Deploy**
   - Railway automatically deploys on every push to main
   - Or click "Deploy" button to deploy manually
   - Wait for deployment to complete (usually 2-3 minutes)

6. **Get Your URL**
   - Go to your web service → "Settings"
   - Copy the "Public Domain" URL (e.g., `your-app.railway.app`)

7. **Set Telegram Webhook**
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
        -H "Content-Type: application/json" \
        -d '{"url": "https://your-app.railway.app/webhook"}'
   ```

8. **Verify Deployment**
   - Visit `https://your-app.railway.app/` in browser
   - Should see "Telegram Language Buddy Bot is running!"
   - Send a message to your bot on Telegram

### Railway Tips

- **Monitor Usage**: Check "Usage" tab to see credit consumption
- **View Logs**: Click "Deployments" → Select deployment → "View Logs"
- **Custom Domain**: Add your own domain in "Settings" → "Networking"
- **Scaling**: Upgrade to paid plan if you exceed free credit

---

## 🎨 Render Deployment

### Why Render?
- ✅ Free forever (with limitations)
- ✅ Automatic PostgreSQL
- ✅ Easy setup
- ⚠️ Services sleep after 15 min inactivity (wake takes ~30 sec)

### Step-by-Step Guide

1. **Sign Up**
   - Go to [render.com](https://render.com)
   - Sign in with GitHub

2. **Create PostgreSQL Database**
   - Click "New" → "PostgreSQL"
   - Name: `telegram-bot-db`
   - Plan: **Free**
   - Region: Choose closest to you
   - Click "Create Database"
   - **Note the connection string** (you'll need it)

3. **Create Web Service**
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Select `telegram-language-buddy-bot`

4. **Configure Service**
   - **Name**: `telegram-language-buddy-bot` (or any name)
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: (leave empty)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn src.main:app`

5. **Set Environment Variables**
   - Scroll to "Environment Variables"
   - Add:
     ```
     FLASK_ENV=production
     TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
     DATABASE_URL=<paste connection string from PostgreSQL service>
     ```
   - Optional voice transcription keys

6. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy (first time: 5-10 minutes)
   - Wait for "Live" status

7. **Get Your URL**
   - Your service URL: `your-app.onrender.com`
   - Render provides this automatically

8. **Set Telegram Webhook**
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
        -H "Content-Type: application/json" \
        -d '{"url": "https://your-app.onrender.com/webhook"}'
   ```

### Render Tips

- **Sleep Mode**: Free services sleep after 15 min. First request after sleep takes ~30 sec
- **Keep-Alive**: Use a service like [UptimeRobot](https://uptimerobot.com) to ping your bot every 5 minutes (free)
- **View Logs**: Click "Logs" tab in your service
- **Database**: Free PostgreSQL has 90-day data retention limit

---

## 🪰 Fly.io Deployment (Alternative)

### Why Fly.io?
- ✅ Generous free tier
- ✅ No sleep delays
- ✅ Global edge network
- ⚠️ Slightly more complex setup

### Quick Setup

1. **Install Fly CLI**
   ```bash
   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   
   # Mac/Linux
   curl -L https://fly.io/install.sh | sh
   ```

2. **Sign Up & Login**
   ```bash
   fly auth signup
   fly auth login
   ```

3. **Create App**
   ```bash
   fly launch
   ```
   - Follow prompts
   - Select region
   - Don't deploy yet (we need to configure first)

4. **Add PostgreSQL**
   ```bash
   fly postgres create --name telegram-bot-db
   fly postgres attach telegram-bot-db
   ```

5. **Set Secrets**
   ```bash
   fly secrets set TELEGRAM_BOT_TOKEN=your_token
   fly secrets set FLASK_ENV=production
   ```

6. **Deploy**
   ```bash
   fly deploy
   ```

7. **Set Webhook**
   ```bash
   # Get your app URL
   fly status
   
   # Set webhook
   curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
        -d '{"url": "https://your-app.fly.dev/webhook"}'
   ```

---

## 🔧 Troubleshooting

### Railway Issues

**Deployment fails:**
- Check logs in Railway dashboard
- Verify all environment variables are set
- Ensure `requirements.txt` is correct

**Database connection errors:**
- Verify `DATABASE_URL` is automatically set (check Variables tab)
- Ensure PostgreSQL service is running

### Render Issues

**Service won't start:**
- Check build logs for errors
- Verify `gunicorn` is in `requirements.txt`
- Ensure start command is correct: `gunicorn src.main:app`

**Slow first response:**
- Normal! Service wakes from sleep (~30 sec)
- Use UptimeRobot to keep it awake

**Database connection:**
- Verify `DATABASE_URL` is set correctly
- Check PostgreSQL service is running
- Ensure database and web service are in same region

### General Issues

**Webhook not working:**
- Verify your bot URL is accessible: `curl https://your-app.domain/webhook`
- Check Telegram webhook status:
  ```bash
  curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
  ```

**Import errors:**
- Ensure you're using `gunicorn src.main:app` (not `python src/main.py`)
- Verify all dependencies in `requirements.txt`

---

## 💰 Cost Comparison

| Platform | Monthly Cost | Database | Limitations |
|----------|--------------|----------|-------------|
| **Railway** | $0 (free credit) | Included | $5 credit/month |
| **Render** | $0 | Included | Sleeps after 15 min |
| **Fly.io** | $0 | Separate | Limited resources |
| **Heroku** | ~$12 | $5 addon | No free tier |

**Recommendation**: Start with **Railway** for the best free experience!

---

## 🚀 Next Steps

1. Choose a platform (Railway recommended)
2. Follow the step-by-step guide above
3. Test your bot on Telegram
4. Monitor usage and logs
5. Set up alerts if needed

Happy deploying! 🎉




