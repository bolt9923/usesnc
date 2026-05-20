"""Shared helpers for SNC Userbot plugins."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from telethon.errors import FloodWaitError, MessageIdInvalidError, MessageNotModifiedError

logger = logging.getLogger(__name__)

MEDIA_KWARGS = {"file", "media", "thumb", "attributes", "buttons"}


def is_self_event(event: Any) -> bool:
    """Return True when a command message was sent by the logged-in user."""
    return bool(getattr(event, "out", False) or getattr(event, "outgoing", False))


async def respond(event: Any, *args: Any, **kwargs: Any) -> Any:
    """
    Reply/edit helper used by commands.

    For outgoing/self .commands, text-only responses edit the command message.
    For incoming events, or when media/buttons are being sent, it falls back to reply().
    """
    has_media = any(key in kwargs and kwargs.get(key) is not None for key in MEDIA_KWARGS)

    if is_self_event(event) and not has_media:
        try:
            text = args[0] if args else kwargs.pop("message", "")
            return await event.edit(text, **kwargs)
        except MessageNotModifiedError:
            return event
        except (MessageIdInvalidError, TypeError, ValueError):
            # Some events/messages cannot be edited; reply is the safe fallback.
            pass
        except Exception as exc:
            logger.debug("edit fallback to reply: %s", exc)

    return await event.reply(*args, **kwargs)


async def safe_edit(target: Any, text: str, **kwargs: Any) -> Any:
    """Edit a Telethon event/message and ignore harmless edit errors."""
    try:
        return await target.edit(text, **kwargs)
    except MessageNotModifiedError:
        return target


async def safe_delete(target: Any) -> bool:
    """Delete a message/event without raising non-critical errors."""
    try:
        await target.delete()
        return True
    except Exception as exc:
        logger.debug("delete ignored: %s", exc)
        return False


async def flood_sleep(seconds: int | float) -> None:
    """Yield control while sleeping; keeps delays non-negative."""
    await asyncio.sleep(max(float(seconds), 0.0))


async def run_flood_safe(coro: Any) -> Any:
    """Run a Telegram request and transparently handle FloodWait once."""
    try:
        return await coro
    except FloodWaitError as exc:
        wait_for = int(getattr(exc, "seconds", 0)) + 1
        logger.warning("FloodWait: sleeping for %ss", wait_for)
        await asyncio.sleep(wait_for)
        return await coro


def mark_plugin_loaded(client: Any, name: str) -> bool:
    """
    Prevent duplicate event handler registration on the same client.

    Returns True when the caller should continue loading the plugin.
    """
    loaded = getattr(client, "_snc_loaded_plugins", None)
    if loaded is None:
        loaded = set()
        setattr(client, "_snc_loaded_plugins", loaded)

    if name in loaded:
        return False

    loaded.add(name)
    return True
