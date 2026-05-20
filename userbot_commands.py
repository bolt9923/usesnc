import asyncio
import random

from telethon import events
from telethon.errors import FloodWaitError

from utils import mark_plugin_loaded, respond

# ================= STATES =================
tag_running = {}
tag_paused = {}
auto_react = {}
auto_clone = {}

tag_delay = {}
utag_delay = {}
tagall_delay = {}

DEFAULT_DELAY = 2


async def _safe_send(client, chat_id, message, **kwargs):
    try:
        return await client.send_message(chat_id, message, **kwargs)
    except FloodWaitError as exc:
        await asyncio.sleep(int(exc.seconds) + 1)
        return await client.send_message(chat_id, message, **kwargs)


# ================= LOAD USERBOT =================
async def load_userbot(client):
    if not mark_plugin_loaded(client, "userbot_commands"):
        return

    me = await client.get_me()
    owner_id = me.id

    print("🔥 SHINU USERBOT LOADED")

    # ================= PING =================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.ping$"))
    async def ping(event):
        await respond(event, "🏓 PONG")

    # ================= HELP =================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.help$"))
    async def help_cmd(event):
        text = """
🔥 SHINU USERBOT 🔥

.ping
.help

.starttag
.stop
.pausetag
.resumetag

.tagall text
.utag (reply)

.reaction on
.reaction off

.clone on
.clone off

.settagdelay 2
.setutagdelay 2
.settagalldelay 2

📦 STICKER SYSTEM
.sticker on
.sticker off
.setstickerdelay 2
.setstickerpack pack_link_or_shortname
""".strip()
        await respond(event, text)

    # ================= STOP =================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.stop$"))
    async def stop(event):
        tag_running[owner_id] = False
        await respond(event, "🛑 STOPPED")

    # ================= PAUSE =================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.pausetag$"))
    async def pause(event):
        tag_paused[owner_id] = True
        await respond(event, "⏸ PAUSED")

    # ================= RESUME =================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.resumetag$"))
    async def resume(event):
        tag_paused[owner_id] = False
        await respond(event, "▶️ RESUMED")

    # ================= DELAYS =================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.settagdelay (\d+)$"))
    async def set_tag_delay(event):
        tag_delay[owner_id] = max(int(event.pattern_match.group(1)), 1)
        await respond(event, f"✅ TAG DELAY SET: {tag_delay[owner_id]}s")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.setutagdelay (\d+)$"))
    async def set_utag_delay(event):
        utag_delay[owner_id] = max(int(event.pattern_match.group(1)), 1)
        await respond(event, f"✅ UTAG DELAY SET: {utag_delay[owner_id]}s")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.settagalldelay (\d+)$"))
    async def set_tagall_delay(event):
        tagall_delay[owner_id] = max(int(event.pattern_match.group(1)), 1)
        await respond(event, f"✅ TAGALL DELAY SET: {tagall_delay[owner_id]}s")

    # ================= STARTTAG =================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.starttag$"))
    async def starttag(event):
        if tag_running.get(owner_id):
            return await respond(event, "⚠️ Already running")

        tag_running[owner_id] = True
        delay = tag_delay.get(owner_id, DEFAULT_DELAY)
        count = 0

        await respond(event, "🚀 STARTTAG")

        async for user in client.iter_participants(event.chat_id):
            if not tag_running.get(owner_id):
                break

            while tag_paused.get(owner_id):
                await asyncio.sleep(1)

            if getattr(user, "bot", False):
                continue

            name = user.first_name or "User"
            try:
                await _safe_send(
                    client,
                    event.chat_id,
                    f"[{name}](tg://user?id={user.id}) hi",
                    parse_mode="md",
                )
                count += 1
                await asyncio.sleep(delay)
            except Exception:
                continue

        tag_running[owner_id] = False
        await respond(event, f"✅ DONE {count}")

    # ================= TAGALL =================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.tagall (.+)$"))
    async def tagall(event):
        text = event.pattern_match.group(1)
        delay = tagall_delay.get(owner_id, DEFAULT_DELAY)
        count = 0

        await respond(event, "🚀 TAGALL STARTED")

        async for user in client.iter_participants(event.chat_id):
            if getattr(user, "bot", False):
                continue

            name = user.first_name or "User"
            try:
                await _safe_send(
                    client,
                    event.chat_id,
                    f"[{name}](tg://user?id={user.id}) {text}",
                    parse_mode="md",
                )
                count += 1
                await asyncio.sleep(delay)
            except Exception:
                continue

        await respond(event, f"✅ TAGALL DONE ({count})")

    # ================= UTAG =================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.utag$"))
    async def utag(event):
        if not event.is_reply:
            return await respond(event, "⚠️ Reply required")

        reply = await event.get_reply_message()
        reply_text = reply.text if reply else ""
        delay = utag_delay.get(owner_id, DEFAULT_DELAY)
        count = 0

        await respond(event, "🚀 UTAG STARTED")

        async for user in client.iter_participants(event.chat_id):
            if getattr(user, "bot", False):
                continue

            name = user.first_name or "User"
            try:
                await _safe_send(
                    client,
                    event.chat_id,
                    f"[{name}](tg://user?id={user.id}) {reply_text}",
                    parse_mode="md",
                )
                count += 1
                await asyncio.sleep(delay)
            except Exception:
                continue

        await respond(event, f"✅ UTAG DONE ({count})")

    # ================= REACTION =================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.reaction on$"))
    async def react_on(event):
        auto_react[owner_id] = True
        await respond(event, "✅ REACTION ON")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.reaction off$"))
    async def react_off(event):
        auto_react[owner_id] = False
        await respond(event, "❌ REACTION OFF")

    @client.on(events.NewMessage(incoming=True))
    async def reaction_handler(event):
        if not auto_react.get(owner_id):
            return

        try:
            await event.react(random.choice(["🔥", "👍", "❤️"]))
        except Exception:
            pass

    # ================= CLONE =================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.clone on$"))
    async def clone_on(event):
        auto_clone[owner_id] = True
        await respond(event, "✅ CLONE ON")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.clone off$"))
    async def clone_off(event):
        auto_clone[owner_id] = False
        await respond(event, "❌ CLONE OFF")

    print("🔥 ALL COMMANDS LOADED")
