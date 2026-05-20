from telethon import events
import json
import random
import asyncio
import os
from utils import respond, mark_plugin_loaded, safe_delete

DB_FILE = "reraid_db.json"

# ================= REPLIES ================= #

REPLIES = [
    "🔥 Auto reply active",
    "⚡ SNC USERBOT",
    "👀 Message detected",
    "😎 Reply triggered",
    "🚀 User detected"
]

# ================= DATABASE ================= #

def load_db():

    if not os.path.exists(DB_FILE):

        data = {
            "enabled": True,
            "users": [],
            "count": 1
        }

        with open(DB_FILE, "w") as f:
            json.dump(data, f, indent=4)

        return data

    try:

        with open(DB_FILE, "r") as f:
            return json.load(f)

    except:

        return {
            "enabled": True,
            "users": [],
            "count": 1
        }


def save_db():

    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)


db = load_db()

# ================= RANDOM REPLY ================= #

def get_reply():

    return random.choice(REPLIES)

# ================= LOAD FUNCTION ================= #

def load_reraid(client):

    if not mark_plugin_loaded(client, "reraid"):
        return

    print("✅ ReRaid Plugin Loaded")

    # ================= ADD USER ================= #

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.reraid (.+)$"))
    async def add_user(event):

        try:

            user = event.pattern_match.group(1)

            user = user.replace("@", "").lower().strip()

            if user in db["users"]:

                return await respond(event, 
                    "⚠ User already added"
                )

            db["users"].append(user)

            save_db()

            await respond(event, 
                f"✅ Added @{user}"
            )

        except Exception as e:

            print("ADD USER ERROR:", e)

    # ================= DELETE USER ================= #

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.delreraid (.+)$"))
    async def del_user(event):

        try:

            user = event.pattern_match.group(1)

            user = user.replace("@", "").lower().strip()

            if user not in db["users"]:

                return await respond(event, 
                    "❌ User not found"
                )

            db["users"].remove(user)

            save_db()

            await respond(event, 
                f"✅ Removed @{user}"
            )

        except Exception as e:

            print("DELETE USER ERROR:", e)

    # ================= LIST USERS ================= #

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.rlist$"))
    async def list_users(event):

        try:

            if not db["users"]:

                return await respond(event, 
                    "❌ No users added"
                )

            text = "🔥 Reply Raid Users\n\n"

            for user in db["users"]:

                text += f"• @{user}\n"

            await respond(event, text)

        except Exception as e:

            print("LIST ERROR:", e)

    # ================= COUNT ================= #

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.rcount (\d+)$"))
    async def set_count(event):

        try:

            count = int(
                event.pattern_match.group(1)
            )
            count = max(1, min(count, 10))

            db["count"] = count

            save_db()

            await respond(event, 
                f"✅ Count set to {count}"
            )

        except Exception as e:

            print("COUNT ERROR:", e)

    # ================= ENABLE / DISABLE ================= #

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.rraid (on|off)$"))
    async def toggle(event):

        try:

            mode = event.pattern_match.group(1)

            if mode == "on":

                db["enabled"] = True

                save_db()

                return await respond(event, 
                    "✅ Reply raid enabled"
                )

            db["enabled"] = False

            save_db()

            await respond(event, 
                "❌ Reply raid disabled"
            )

        except Exception as e:

            print("TOGGLE ERROR:", e)

    # ================= AUTO REPLY ================= #

    @client.on(events.NewMessage(incoming=True))
    async def auto_reply(event):

        try:

            # ENABLE CHECK
            if not db["enabled"]:
                return

            # GROUP ONLY
            if not event.is_group:
                return

            # REPLY ONLY
            if not event.is_reply:
                return

            # GET SENDER
            sender = await event.get_sender()

            if not sender:
                return

            # USERNAME
            username = ""

            if sender.username:
                username = sender.username.lower().strip()

            # USER ID
            user_id = str(sender.id)

            # TARGETS
            targets = [
                str(x).lower().strip()
                for x in db["users"]
            ]

            print("USERNAME:", username)
            print("USER_ID:", user_id)
            print("TARGETS:", targets)

            # MATCH CHECK
            if (
                username not in targets
                and
                user_id not in targets
            ):
                return

            print("🔥 TARGET DETECTED")

            # AUTO REPLY
            for _ in range(int(db["count"])):

                text = get_reply()

                await respond(event, text)

                await asyncio.sleep(0.5)

        except Exception as e:

            print("AUTO REPLY ERROR:", e)
