import os

from telethon import events, functions
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import (
    UploadProfilePhotoRequest,
    DeletePhotosRequest
)
from utils import respond, mark_plugin_loaded, safe_delete

# =========================
# DEFAULT PROFILE
# =========================
OWNER = os.environ.get("OWNER", "SNC USER")
BIO = os.environ.get("BIO", "SNC USERBOT")

# =========================
# STORAGE
# =========================
original_profile = {}

# =========================
# LOAD PLUGIN
# =========================
def load_clone(client):

    if not mark_plugin_loaded(client, "clone"):
        return

    print("✅ clone plugin loaded")

    # =========================
    # CLONE COMMAND
    # =========================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.clone(?:\s+(?!on$|off$)(.+))?$"))
    async def clone(event):

        try:

            target = None

            # ---------------- REPLY MODE ----------------
            if event.is_reply:

                reply = await event.get_reply_message()

                target = await reply.get_sender()

            # ---------------- USERNAME MODE ----------------
            else:

                text = event.pattern_match.group(1)

                if not text:

                    return await respond(event, 
                        "❌ Reply to user or give username\n\n"
                        "Example:\n.clone @username"
                    )

                target = await client.get_entity(text)

            # ---------------- SAVE ORIGINAL PROFILE ----------------
            me = await client.get_me()

            if not original_profile:

                original_profile["first_name"] = me.first_name or OWNER
                original_profile["last_name"] = me.last_name or ""
                original_profile["bio"] = BIO

            # ================= GET TARGET BIO =================
            bio = ""

            try:

                full = await client(
                    functions.users.GetFullUserRequest(target.id)
                )

                bio = full.full_user.about or ""

            except Exception as e:

                print("BIO ERROR:", e)

            # ================= UPDATE PROFILE =================
            await client(
                UpdateProfileRequest(
                    first_name=target.first_name or "",
                    last_name=target.last_name or "",
                    about=bio
                )
            )

            # ================= DELETE OLD PROFILE PHOTO =================
            try:

                photos = []

                async for photo in client.iter_profile_photos("me"):
                    photos.append(photo)

                if photos:

                    await client(
                        DeletePhotosRequest(
                            id=[photos[0]]
                        )
                    )

            except Exception as e:

                print("DELETE PHOTO ERROR:", e)

            # ================= DOWNLOAD TARGET PHOTO =================
            path = None

            try:

                path = await client.download_profile_photo(
                    target.id,
                    file="clone.jpg"
                )

            except Exception as e:

                print("DOWNLOAD PHOTO ERROR:", e)

            # ================= UPLOAD TARGET PHOTO =================
            if path:

                try:

                    if os.path.exists(path):

                        file = await client.upload_file(path)

                        await client(
                            UploadProfilePhotoRequest(
                                file=file
                            )
                        )

                        print("PHOTO CLONED")

                except Exception as e:

                    print("UPLOAD PHOTO ERROR:", e)

            else:

                print("NO PROFILE PHOTO")

            # ================= SUCCESS =================
            await respond(event, 
                f"✅ Successfully cloned:\n{target.first_name}"
            )

        except Exception as e:

            print("CLONE ERROR:", e)

            await respond(event, 
                f"❌ Clone Failed:\n{e}"
            )

    # =========================
    # REVERT COMMAND
    # =========================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.revert$"))
    async def revert(event):

        try:

            # ================= RESTORE PROFILE =================
            await client(
                UpdateProfileRequest(
                    first_name=original_profile.get(
                        "first_name",
                        OWNER
                    ),
                    last_name=original_profile.get(
                        "last_name",
                        ""
                    ),
                    about=original_profile.get(
                        "bio",
                        BIO
                    )
                )
            )

            # ================= DELETE CLONED PHOTO =================
            try:

                photos = []

                async for photo in client.iter_profile_photos("me"):
                    photos.append(photo)

                if photos:

                    await client(
                        DeletePhotosRequest(
                            id=[photos[0]]
                        )
                    )

            except Exception as e:

                print("DELETE ERROR:", e)

            await respond(event, 
                "✅ Profile reverted successfully"
            )

        except Exception as e:

            print("REVERT ERROR:", e)

            await respond(event, 
                f"❌ Revert Failed:\n{e}"
            )

    # =========================
    # TEST COMMAND
    # =========================
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.testclone$"))
    async def testclone(event):

        await respond(event, 
            "✅ Clone Plugin Working"
        )
