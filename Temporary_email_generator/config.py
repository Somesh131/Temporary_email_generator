import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file")

# Temp mail API configuration
MAIL_API_BASE = "https://api.mail.tm"
MAIL_DOMAINS_ENDPOINT = f"{MAIL_API_BASE}/domains"
MAIL_ACCOUNTS_ENDPOINT = f"{MAIL_API_BASE}/accounts"
MAIL_MESSAGES_ENDPOINT = f"{MAIL_API_BASE}/messages"

# Bot settings
MAX_EMAILS_PER_USER = 5
MESSAGE_CHECK_INTERVAL = 30  # seconds