# SNC Userbot Patch Notes

## Main fixes
- Added `utils.respond()` so text responses from self-sent `.commands` edit the command message instead of replying.
- Made plugin command handlers self/outgoing-only wherever they were missing it.
- Added duplicate plugin registration protection with `mark_plugin_loaded()`.
- Added active userbot client tracking so restored/logged-in clients stay alive and old duplicate sessions disconnect cleanly.
- Fixed missing `functions` imports in QuotLy and SangMata plugins.
- Replaced the broken legacy root `raid.py` Pyrogram module with a safe compatibility wrapper for the existing Telethon plugin.

## Async / stability improvements
- Stream participants with `iter_participants()` instead of loading whole groups into memory.
- Added FloodWait handling in tag, sticker, broadcast and repeat-message flows.
- Added sticker-pack caching so sticker loop does not fetch the pack on every send.
- Added real `.stopspam` cancellation for the repeat-message task.
- Anchored command regex patterns to reduce accidental triggers.

## Note
Media-producing commands such as `.q` still send the generated media separately because Telegram text-message edits cannot always replace the command with a media message reliably. Text status/errors for self commands are edited.
