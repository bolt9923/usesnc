import asyncio
import random

from telethon import events
from telethon.errors import FloodWaitError
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import InputStickerSetShortName

from utils import mark_plugin_loaded, respond

# ================= STATE =================
sticker_on = {}
sticker_delay = {}
sticker_pack = {}
sticker_cache = {}
sticker_task = {}


async def get_pack_documents(client, pack_name):
    cached = sticker_cache.get(pack_name)
    if cached:
        return cached

    result = await client(GetStickerSetRequest(
        stickerset=InputStickerSetShortName(pack_name),
        hash=0,
    ))
    documents = list(result.documents or []) if result else []
    if documents:
        sticker_cache[pack_name] = documents
    return documents


# ================= LOAD =================
def load_stickers(client):
    if not mark_plugin_loaded(client, "stickers"):
        return

    print("🟢 STICKER SYSTEM LOADED")

    # ================= ON =================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.sticker on$"))
    async def on(event):
        uid = event.sender_id
        sticker_on[uid] = True
        await respond(event, "✅ STICKER ON")

        # start loop only once
        if uid not in sticker_task or sticker_task[uid].done():
            sticker_task[uid] = asyncio.create_task(
                sticker_loop(client, event.chat_id, uid)
            )

    # ================= OFF =================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.sticker off$"))
    async def off(event):
        uid = event.sender_id
        sticker_on[uid] = False

        task = sticker_task.get(uid)
        if task and not task.done():
            task.cancel()

        await respond(event, "❌ STICKER OFF")

    # ================= DELAY =================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.setstickerdelay (\d+)$"))
    async def delay(event):
        value = max(int(event.pattern_match.group(1)), 1)
        sticker_delay[event.sender_id] = value
        await respond(event, f"⏱ DELAY SET: {value}s")

    # ================= PACK =================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.setstickerpack (.+)$"))
    async def pack(event):
        raw = event.pattern_match.group(1).strip()
        pack_name = raw.rstrip("/").split("/")[-1].strip()

        try:
            documents = await get_pack_documents(client, pack_name)
            if not documents:
                return await respond(event, "❌ Invalid Sticker Pack")

            sticker_pack[event.sender_id] = pack_name
            await respond(event, f"📦 PACK SAVED:\n{pack_name}\nStickers cached: {len(documents)}")
        except Exception as e:
            await respond(event, f"❌ ERROR:\n{e}")

    print("🔥 STICKER SYSTEM READY")


# ================= LOOP ENGINE =================
async def sticker_loop(client, chat_id, uid):
    try:
        while sticker_on.get(uid, False):
            pack = sticker_pack.get(uid)
            if not pack:
                await asyncio.sleep(2)
                continue

            delay = sticker_delay.get(uid, 2)

            try:
                documents = await get_pack_documents(client, pack)
                if documents:
                    await client.send_file(chat_id, random.choice(documents))
            except FloodWaitError as exc:
                await asyncio.sleep(int(exc.seconds) + 1)
            except Exception as e:
                print("STICKER LOOP ERROR:", e)

            await asyncio.sleep(delay)
    except asyncio.CancelledError:
        pass
