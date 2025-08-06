#!/bin/bash
# Deployment script for Heroku with database backup/restore

echo "🚀 Starting deployment process..."

# Step 1: Backup current database
echo "📋 Backing up current database..."
python backup_db.py

if [ $? -eq 0 ]; then
    echo "✅ Database backup completed"
else
    echo "⚠️  Database backup failed, continuing anyway..."
fi

# Step 2: Deploy to Heroku
echo "🌐 Deploying to Heroku..."
git add .
git commit -m "Auto-deploy with database backup $(date)"

git push heroku main

if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"
    echo "🔗 App URL: https://telegram-language-buddy-bot-20b6ba66423e.herokuapp.com/"
else
    echo "❌ Deployment failed!"
    exit 1
fi

echo "🎉 Deployment process completed!" 