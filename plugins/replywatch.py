import asyncio
import random
import time

from telethon import events

from utils import mark_plugin_loaded, respond

reply_watch = {}
last_reply_time = {}


def load_replywatch(client):
    if not mark_plugin_loaded(client, "replywatch"):
        return

    print("✅ ReplyWatch Loaded")

    # =========================
    # ADD WATCH
    # =========================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.replywatch (.+?) (\d+)$"))
    async def add_watch(event):
        user = event.pattern_match.group(1).replace("@", "").lower().strip()
        delay = max(int(event.pattern_match.group(2)), 0)

        messages = [
            "👀 Message detected",
            "🔥 SNC USERBOT ACTIVE",
            "⚡ Auto reply running",
            "😎 User triggered response",
            "💬 Hello there",
        ]

        reply_watch[user] = {
            "delay": delay,
            "messages": messages,
        }

        await respond(
            event,
            f"✅ Reply watch enabled\n👤 User: {user}\n⏱ Delay: {delay} sec",
        )

    # =========================
    # AUTO REPLY
    # =========================
    @client.on(events.NewMessage(incoming=True))
    async def auto_reply(event):
        try:
            sender = await event.get_sender()
            if not sender:
                return

            username = sender.username.lower() if getattr(sender, "username", None) else ""
            user_id = str(sender.id)
            matched = username if username in reply_watch else user_id if user_id in reply_watch else None

            if not matched:
                return

            now = time.time()
            if matched in last_reply_time and now - last_reply_time[matched] < 5:
                return

            last_reply_time[matched] = now
            data = reply_watch[matched]
            await asyncio.sleep(data["delay"])
            await respond(event, random.choice(data["messages"]))

        except Exception as e:
            print("AUTO REPLY ERROR:", e)
