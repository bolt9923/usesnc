import asyncio

from telethon import events
from telethon.errors import FloodWaitError

from utils import mark_plugin_loaded, respond, safe_edit


async def _send_or_forward(client, chat_id, text, reply):
    try:
        if reply:
            return await reply.forward_to(chat_id)
        return await client.send_message(chat_id, text)
    except FloodWaitError as exc:
        await asyncio.sleep(int(exc.seconds) + 1)
        if reply:
            return await reply.forward_to(chat_id)
        return await client.send_message(chat_id, text)


# =========================
# LOAD BROADCAST
# =========================
def load_broadcast(client):
    if not mark_plugin_loaded(client, "broadcast"):
        return

    print("✅ Broadcast Plugin Loaded")

    # =========================
    # GROUP GCAST
    # =========================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.gcast(?:\s|$)(.*)"))
    async def gcast(event):
        text = event.pattern_match.group(1).strip()
        reply = await event.get_reply_message()

        if not text and not reply:
            return await respond(event, "❌ Give message or reply")

        msg = await respond(event, "📢 Starting Group Broadcast...")
        done = 0
        failed = 0

        async for dialog in client.iter_dialogs():
            if not dialog.is_group:
                continue

            try:
                await _send_or_forward(client, dialog.id, text, reply)
                done += 1
                await asyncio.sleep(1)
            except Exception:
                failed += 1

        await safe_edit(
            msg,
            f"✅ GCAST DONE\n\n✔️ Success: {done}\n❌ Failed: {failed}",
        )

    # =========================
    # PRIVATE GUCAST
    # =========================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.gucast(?:\s|$)(.*)"))
    async def gucast(event):
        text = event.pattern_match.group(1).strip()
        reply = await event.get_reply_message()

        if not text and not reply:
            return await respond(event, "❌ Give message or reply")

        msg = await respond(event, "📨 Starting User Broadcast...")
        done = 0
        failed = 0

        async for dialog in client.iter_dialogs():
            if not dialog.is_user:
                continue

            try:
                await _send_or_forward(client, dialog.id, text, reply)
                done += 1
                await asyncio.sleep(1)
            except Exception:
                failed += 1

        await safe_edit(
            msg,
            f"✅ GUCAST DONE\n\n✔️ Success: {done}\n❌ Failed: {failed}",
        )
