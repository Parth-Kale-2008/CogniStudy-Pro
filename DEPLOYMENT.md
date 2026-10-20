# 🚀 CogniStudy Pro™ — Deployment & Operations Manual

> **Zero-to-production deployment guide for containerized clouds, PaaS hosts, and VPS servers.**

---

## 📦 Deployment Options Overview

| Platform | Difficulty | Recommended Use | Auto SSL |
|---|---|---|---|
| **Docker Compose** | Easy | VPS / On-Premise / Dev | Manual / Caddy |
| **Railway / Render** | Beginner | Cloud PaaS (1-Click) | ✅ Yes |
| **Fly.io** | Intermediate | Global Edge Deployment | ✅ Yes |
| **Ubuntu VPS (systemd)** | Intermediate | Self-hosted production | Via Nginx / Certbot |

---

## 🐳 Option 1: Docker Compose (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd StudyMate
   ```
2. **Create your `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API Key and Telegram Token
   ```
3. **Launch the container stack:**
   ```bash
   docker-compose up -d --build
   ```
4. **Verify Health:**
   ```bash
   curl http://localhost:8000/health
   ```

---

## ☁️ Option 2: Railway / Render (1-Click Cloud)

1. Fork or push this repository to GitHub.
2. In **Railway** or **Render**, click **New Service** -> **GitHub Repo**.
3. Set the environment variables in the dashboard:
   * `ENVIRONMENT`: `production`
   * `OPENAI_API_KEY`: `sk-proj-...`
   * `TELEGRAM_BOT_TOKEN`: `...` (optional)
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Health Check Path: `/health`

---

## 🤖 Option 3: 24/7 Telegram Webhook Setup

To connect your 24/7 Telegram Bot to your deployed service:

1. Create a bot with `@BotFather` on Telegram and copy your API token.
2. Add the token to your `.env` file:
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
   ```
3. Set your webhook with Telegram:
   ```bash
   curl -F "url=https://your-domain.com/telegram-webhook" https://api.telegram.org/bot<YOUR_TELEGRAM_BOT_TOKEN>/setWebhook
   ```
4. Verify webhook status:
   ```bash
   curl https://api.telegram.org/bot<YOUR_TELEGRAM_BOT_TOKEN>/getWebhookInfo
   ```

Now users can upload files and ask questions 24/7 via Telegram!
