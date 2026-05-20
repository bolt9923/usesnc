"""
Manual message repeat plugin.
Commands:
  .spam <count> <message>
  .delspam <count> <message>
  .fspam <message>
  .stopspam
"""

import asyncio
import logging

from telethon import events
from telethon.errors import FloodWaitError

from utils import mark_plugin_loaded, safe_delete

logger = logging.getLogger(__name__)
spam_tasks = {}


async def _sleep_or_flood(delay):
    await asyncio.sleep(max(float(delay), 0.0))


async def _send_with_flood_wait(client, chat_id, message):
    try:
        return await client.send_message(chat_id, message)
    except FloodWaitError as exc:
        await asyncio.sleep(int(exc.seconds) + 1)
        return await client.send_message(chat_id, message)


def _cancel_old(uid):
    task = spam_tasks.get(uid)
    if task and not task.done():
        task.cancel()


async def _run_spam(client, uid, chat_id, count, message, delay, delete_after=False):
    sent_msgs = []
    try:
        for _ in range(count):
            msg = await _send_with_flood_wait(client, chat_id, message)
            if delete_after and msg:
                sent_msgs.append(msg.id)
            await _sleep_or_flood(delay)

        if delete_after and sent_msgs:
            await asyncio.sleep(5)
            await client.delete_messages(chat_id, sent_msgs)
    except asyncio.CancelledError:
        logger.info("Spam task cancelled for %s", uid)
    except Exception as exc:
        logger.error("Spam task error: %s", exc)
    finally:
        if spam_tasks.get(uid) is asyncio.current_task():
            spam_tasks.pop(uid, None)


def load_spam(client):
    """Load repeat-message plugin."""
    if not mark_plugin_loaded(client, "spam"):
        return

    @client.on(events.NewMessage(pattern=r'^\.spam(?:\s|$)', outgoing=True))
    async def spam_handler(event):
        args = event.pattern_match.string.split(maxsplit=2)
        if len(args) < 3:
            return await event.edit("Usage: `.spam 10 message here`")

        try:
            count = int(args[1])
            if count < 1:
                return await event.edit("❌ Minimum 1")
            if count > 100:
                return await event.edit("❌ Maximum 100")
        except ValueError:
            return await event.edit("❌ Invalid number")

        uid = event.sender_id
        _cancel_old(uid)
        await safe_delete(event)
        spam_tasks[uid] = asyncio.create_task(
            _run_spam(client, uid, event.chat_id, count, args[2], 0.5)
        )

    @client.on(events.NewMessage(pattern=r'^\.delspam(?:\s|$)', outgoing=True))
    async def delspam_handler(event):
        args = event.pattern_match.string.split(maxsplit=2)
        if len(args) < 3:
            return await event.edit("Usage: `.delspam 10 message`")

        try:
            count = int(args[1])
            if count < 1 or count > 50:
                return await event.edit("❌ Range: 1-50")
        except ValueError:
            return await event.edit("❌ Invalid number")

        uid = event.sender_id
        _cancel_old(uid)
        await safe_delete(event)
        spam_tasks[uid] = asyncio.create_task(
            _run_spam(client, uid, event.chat_id, count, args[2], 0.3, delete_after=True)
        )

    @client.on(events.NewMessage(pattern=r'^\.fspam(?:\s|$)', outgoing=True))
    async def fspam_handler(event):
        args = event.pattern_match.string.split(maxsplit=1)
        if len(args) < 2:
            return await event.edit("Usage: `.fspam message`")

        uid = event.sender_id
        _cancel_old(uid)
        await safe_delete(event)
        spam_tasks[uid] = asyncio.create_task(
            _run_spam(client, uid, event.chat_id, 50, args[1], 0.15)
        )

    @client.on(events.NewMessage(pattern=r'^\.stopspam$', outgoing=True))
    async def stopspam_handler(event):
        uid = event.sender_id
        task = spam_tasks.get(uid)
        if task and not task.done():
            task.cancel()
            await event.edit("🛑 Spam stopped")
        else:
            await event.edit("⚠️ No spam task running")
        await asyncio.sleep(2)
        await safe_delete(event)

    logger.info("✅ Repeat-message plugin loaded")


load = load_spam
init = load_spam
