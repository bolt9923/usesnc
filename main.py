import asyncio
import logging
import os
import re
from typing import Dict, Any

from motor.motor_asyncio import AsyncIOMotorClient
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession

# ================= IMPORT PLUGINS =================
from userbot_commands import load_userbot
from sticker import load_stickers

from plugins.replywatch import load_replywatch
from plugins.clone import load_clone
from plugins.quotly import load_quotly
from plugins.banall import load_banall
from plugins.broadcast import load_broadcast
from plugins.sangmata import load_sangmata
from plugins.reraid import load_reraid
from plugins.spam import load_spam
from plugins.raid import load_raid

# ================= LOGGING =================
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("snc-userbot")

# ================= CONFIG =================
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
MONGO_URL = os.environ["MONGO_URL"]

# ================= MONGO =================
mongo = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=10000)
db = mongo["userbot"]
users = db["users"]

# ================= BOT CLIENT =================
bot = TelegramClient("bot", API_ID, API_HASH)

# ================= STATES =================
user_state: Dict[int, Dict[str, Any]] = {}
active_userbots: Dict[int, TelegramClient] = {}

SYNC_PLUGIN_LOADERS = (
    load_stickers,
    load_replywatch,
    load_clone,
    load_quotly,
    load_banall,
    load_broadcast,
    load_sangmata,
    load_reraid,
    load_spam,
    load_raid,
)

# ================= VALIDATION =================
def is_valid(phone: str) -> bool:
    return bool(re.match(r"^\+[1-9]\d{7,14}$", phone.strip()))


async def install_plugins(client: TelegramClient) -> None:
    """Register all userbot handlers once per client."""
    await load_userbot(client)
    for loader in SYNC_PLUGIN_LOADERS:
        loader(client)


async def activate_userbot(uid: int, client: TelegramClient) -> None:
    """Replace old client for this uid, install plugins, and keep it alive."""
    old_client = active_userbots.get(uid)
    if old_client and old_client.is_connected():
        try:
            await old_client.disconnect()
        except Exception as exc:
            logger.warning("Old client disconnect failed for %s: %s", uid, exc)

    await install_plugins(client)
    active_userbots[uid] = client


async def save_session(uid: int, client: TelegramClient) -> None:
    session = client.session.save()
    await users.update_one(
        {"user_id": uid},
        {"$set": {"session": session}},
        upsert=True,
    )


async def finish_login(event, uid: int, client: TelegramClient, message: str) -> None:
    await save_session(uid, client)
    await activate_userbot(uid, client)
    user_state.pop(uid, None)
    await event.reply(message)


# ================= START =================
@bot.on(events.NewMessage(pattern=r"^/start$"))
async def start(event):
    await event.reply(
        "👋 Welcome To SNC USERBOT\n\n"
        "Commands:\n"
        "/login → Login Userbot\n"
        "/status → Check Login Status"
    )


# ================= LOGIN =================
@bot.on(events.NewMessage(pattern=r"^/login$"))
async def login(event):
    uid = event.sender_id

    old = user_state.pop(uid, None)
    if old and old.get("client"):
        try:
            await old["client"].disconnect()
        except Exception:
            pass

    user_state[uid] = {"step": "phone"}
    await event.reply(
        "📱 Send Your Phone Number\n\n"
        "Example:\n"
        "+911234567890"
    )


# ================= STATUS =================
@bot.on(events.NewMessage(pattern=r"^/status$"))
async def status(event):
    uid = event.sender_id
    state = user_state.get(uid)
    client = active_userbots.get(uid)
    logged = bool(client and client.is_connected())

    if not state and not logged:
        return await event.reply("❌ No Active Login")

    await event.reply(
        "📊 STATUS\n\n"
        f"Step: {state.get('step') if state else 'active'}\n"
        f"Logged: {'Yes' if logged else 'No'}"
    )


# ================= MESSAGE HANDLER =================
@bot.on(events.NewMessage)
async def handler(event):
    uid = event.sender_id
    text = (event.raw_text or "").strip()

    if text.startswith("/") or uid not in user_state:
        return

    state = user_state[uid]

    # ================= PHONE STEP =================
    if state["step"] == "phone":
        if not is_valid(text):
            return await event.reply("❌ Invalid Phone Number")

        client = TelegramClient(StringSession(), API_ID, API_HASH)
        try:
            await client.connect()
            await client.send_code_request(text)

            state["phone"] = text
            state["client"] = client
            state["step"] = "otp"

            await event.reply(
                "📩 OTP Sent\n\n"
                "Send OTP Like:\n"
                "1 2 3 4 5"
            )
        except Exception as exc:
            await client.disconnect()
            await event.reply(f"❌ Error:\n{exc}")

    # ================= OTP STEP =================
    elif state["step"] == "otp":
        client = state["client"]
        phone = state["phone"]

        try:
            otp = text.replace(" ", "")
            await client.sign_in(phone, otp)

        except SessionPasswordNeededError:
            state["step"] = "password"
            return await event.reply(
                "🔐 2FA Enabled\n\n"
                "Send Your Password"
            )

        except Exception as exc:
            return await event.reply(f"❌ OTP Error:\n{exc}")

        await finish_login(
            event,
            uid,
            client,
            "✅ LOGIN SUCCESS\n\n🚀 USERBOT ACTIVATED",
        )

    # ================= PASSWORD STEP =================
    elif state["step"] == "password":
        client = state["client"]

        try:
            await client.sign_in(password=text)
        except Exception as exc:
            return await event.reply(f"❌ 2FA Error:\n{exc}")

        await finish_login(
            event,
            uid,
            client,
            "✅ 2FA LOGIN SUCCESS\n\n🚀 USERBOT ACTIVATED",
        )


# ================= AUTO RESTORE =================
async def load_all():
    async for user in users.find({"session": {"$exists": True, "$ne": ""}}):
        uid = user.get("user_id")
        session = user.get("session")
        if not uid or not session:
            continue

        try:
            client = TelegramClient(StringSession(session), API_ID, API_HASH)
            await client.start()
            await activate_userbot(uid, client)
            logger.info("✅ Restored User: %s", uid)
        except Exception as exc:
            logger.exception("❌ Restore Error for %s: %s", uid, exc)


# ================= MAIN =================
async def main():
    await bot.start(bot_token=BOT_TOKEN)
    logger.info("🚀 BOT STARTED")

    await load_all()
    logger.info("✅ ALL USERBOTS RESTORED")

    await bot.run_until_disconnected()


# ================= RUN =================
if __name__ == "__main__":
    asyncio.run(main())
