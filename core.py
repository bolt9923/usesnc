import os
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

# ================= BOT =================
bot = TelegramClient("bot", API_ID, API_HASH)

# ================= USERBOT HOLDER =================
userbot = None

def create_userbot(session: str):
    global userbot
    userbot = TelegramClient(StringSession(session), API_ID, API_HASH)
    return userbot
