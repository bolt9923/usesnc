import asyncio

from telethon import events, functions

from utils import mark_plugin_loaded, respond


def load_quotly(client):
    if not mark_plugin_loaded(client, "quotly"):
        return

    print("✅ quotly plugin loaded")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(q|quotly)(?: |$)(.*)"))
    async def quotly(event):
        try:
            if not event.is_reply:
                return await respond(event, "❌ Reply to a message")

            color = (event.pattern_match.group(2) or "").strip()
            bot_username = "@QuotLyBot"
            status = await respond(event, "⚡ Creating Quote...")

            try:
                bot_entity = await client.get_entity(bot_username)
                await client(functions.contacts.UnblockRequest(bot_entity))
            except Exception:
                pass

            if color:
                await client.send_message(bot_username, f"/qcolor {color}")
                await asyncio.sleep(1)

            reply = await event.get_reply_message()
            await reply.forward_to(bot_username)

            sticker = None
            for _ in range(10):
                await asyncio.sleep(1)
                async for msg in client.iter_messages(bot_username, limit=5):
                    if msg.sticker:
                        sticker = msg
                        break
                if sticker:
                    break

            if sticker:
                await respond(event, file=sticker.media, reply_to=reply.id)
                try:
                    await status.delete()
                except Exception:
                    pass
            else:
                await status.edit("❌ Quote timeout. Try again.")

        except Exception as e:
            print("QUOTLY ERROR:", e)
            await respond(event, f"❌ Error:\n{e}")
