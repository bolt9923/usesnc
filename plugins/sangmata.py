import asyncio

from telethon import events, functions

from utils import mark_plugin_loaded, respond, safe_edit


# =========================
# LOAD SANGMATA
# =========================
def load_sangmata(client):
    if not mark_plugin_loaded(client, "sangmata"):
        return

    print("✅ Sangmata Plugin Loaded")

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.(sg|sa|sangmata)(?:\s|$)(.*)"))
    async def sangmata(event):
        try:
            reply = await event.get_reply_message()
            args = (event.pattern_match.group(2) or "").strip()
            user = None

            if reply:
                user = await reply.get_sender()
            elif args:
                user = await client.get_entity(args)
            else:
                return await respond(event, "❌ Reply or give username/id")

            bot_username = "@SangMataInfo_bot"
            msg = await respond(event, "🔍 Checking name history...")

            try:
                bot_entity = await client.get_entity(bot_username)
                await client.send_message(bot_entity, f"/search_id {user.id}")
            except Exception:
                try:
                    bot_entity = await client.get_entity(bot_username)
                    await client(functions.contacts.UnblockRequest(bot_entity))
                    await client.send_message(bot_entity, f"/search_id {user.id}")
                except Exception as exc:
                    return await safe_edit(msg, f"❌ Bot error:\n{exc}")

            await asyncio.sleep(3)
            texts = []

            async for m in client.iter_messages(bot_username, limit=5):
                if m.text:
                    texts.append(m.text)

            if not texts:
                return await safe_edit(msg, "❌ No history found")

            result = "\n\n".join(texts)
            await safe_edit(msg, result)

        except Exception as e:
            await respond(event, f"❌ Error:\n{e}")
