"""
Ban Commands - Single ban and mass ban
Commands:
  .ban [user] - Ban single user (username/ID/reply)
  .banall - Ban single user (reply only)
  .fuckingallbyshinu - Ban ALL members (mass destruction)
"""

from telethon import TelegramClient, events
from telethon.errors import (
    FloodWaitError, 
    ChatAdminRequiredError, 
    UserAdminInvalidError,
    ChannelInvalidError,
    UserIdInvalidError,
    PeerIdInvalidError
)
from telethon.tl.types import User
import asyncio
import logging
import os
from utils import mark_plugin_loaded, safe_delete

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Config
API_ID = int(os.environ.get("API_ID", 12345678))
API_HASH = os.environ.get("API_HASH", "your_api_hash_here")


async def safe_ban(client, chat_id, user_id, name=None):
    """Ban user with flood wait handling"""
    target = name or user_id
    try:
        await client.edit_permissions(chat_id, user_id, view_messages=False)
        logger.info(f"Banned: {target}")
        return True, None
        
    except FloodWaitError as e:
        logger.warning(f"FloodWait {e.seconds}s for {target}")
        await asyncio.sleep(e.seconds)
        return await safe_ban(client, chat_id, user_id, name)
        
    except UserAdminInvalidError:
        return False, "User is admin"
    except UserIdInvalidError:
        return False, "Invalid user"
    except PeerIdInvalidError:
        return False, "User not found"
    except Exception as e:
        logger.error(f"Ban error {target}: {e}")
        return False, str(e)


async def get_user_from_args(client, args):
    """Get user from username or ID string"""
    if not args:
        return None, None
    
    target = args[0].strip()
    
    # Username with @
    if target.startswith("@"):
        try:
            user = await client.get_entity(target)
            if isinstance(user, User):
                name = user.username or user.first_name or str(user.id)
                return user.id, name
        except Exception as e:
            return None, f"Cannot find {target}: {e}"
    
    # Numeric ID
    if target.isdigit():
        uid = int(target)
        try:
            user = await client.get_entity(uid)
            if isinstance(user, User):
                name = user.username or user.first_name or str(user.id)
                return uid, name
        except Exception as e:
            return None, f"Cannot find ID {uid}: {e}"
    
    # Try as username without @
    try:
        user = await client.get_entity(target)
        if isinstance(user, User):
            name = user.username or user.first_name or str(user.id)
            return user.id, name
    except:
        pass
    
    return None, "Invalid target. Use @username or user ID"


def register_commands(client):
    """Register ban commands"""
    
    # ================= .ban - Single user (flexible) =================
    @client.on(events.NewMessage(pattern=r'^\.ban(?:\s|$)', outgoing=True))
    async def ban_handler(event):
        """Ban single user by username, ID, or reply"""
        chat_id = event.chat_id
        
        # Check perms
        try:
            perms = await client.get_permissions(chat_id, 'me')
            if not perms.is_admin or not perms.ban_users:
                return await event.edit("❌ No ban rights!")
        except Exception as e:
            return await event.edit(f"⚠️ Error: {e}")
        
        # Get target
        args = event.pattern_match.string.split()[1:]
        user_id = None
        name = None
        
        # Check reply first
        if event.is_reply:
            replied = await event.get_reply_message()
            if replied and replied.sender:
                user = replied.sender
                if isinstance(user, User):
                    user_id = user.id
                    name = user.username or user.first_name or str(user.id)
        
        # If no reply, check args
        if user_id is None and args:
            user_id, name = await get_user_from_args(client, args)
            if user_id is None:
                return await event.edit(f"❌ {name}")
        
        if user_id is None:
            return await event.edit("❌ Usage: `.ban @user` or `.ban 123456` or reply to user")
        
        # Ban
        msg = await event.edit(f"🔨 Banning {name}...")
        success, error = await safe_ban(client, chat_id, user_id, name)
        
        if success:
            await msg.edit(f"✅ Banned: {name}")
            await asyncio.sleep(3)
            try:
                await event.delete()
            except:
                pass
        else:
            await msg.edit(f"❌ Failed: {name}\nReason: {error}")
    
    # ================= .banall - Single user (reply only) =================
    @client.on(events.NewMessage(pattern=r'^\.banall$', outgoing=True))
    async def banall_single_handler(event):
        """Ban single user by reply only"""
        chat_id = event.chat_id
        
        # Must be reply
        if not event.is_reply:
            return await event.edit("❌ Reply to a user message with `.banall`")
        
        # Check perms
        try:
            perms = await client.get_permissions(chat_id, 'me')
            if not perms.is_admin or not perms.ban_users:
                return await event.edit("❌ No ban rights!")
        except Exception as e:
            return await event.edit(f"⚠️ Error: {e}")
        
        # Get replied user
        replied = await event.get_reply_message()
        if not replied or not replied.sender:
            return await event.edit("❌ Cannot identify user")
        
        user = replied.sender
        if not isinstance(user, User):
            return await event.edit("❌ Target is not a user")
        
        user_id = user.id
        name = user.username or user.first_name or str(user.id)
        
        # Ban
        msg = await event.edit(f"🔨 Banning {name}...")
        success, error = await safe_ban(client, chat_id, user_id, name)
        
        if success:
            await msg.edit(f"✅ Banned: {name}")
        else:
            await msg.edit(f"❌ Failed: {name}\nReason: {error}")
    
    # ================= .fuckingallbyshinu - MASS BAN =================
    @client.on(events.NewMessage(pattern=r'^\.fuckingallbyshinu$', outgoing=True))
    async def fuckingallbyshinu_handler(event):
        """MASS BAN - Ban ALL members"""
        chat_id = event.chat_id
        
        # Check perms
        try:
            perms = await client.get_permissions(chat_id, 'me')
            if not perms.is_admin:
                return await event.edit("❌ Not admin!")
            if not perms.ban_users:
                return await event.edit("❌ No ban permission!")
        except Exception as e:
            return await event.edit(f"⚠️ Error: {e}")
        
        # Warning message
        msg = await event.edit(
            "⚠️ **MASS BAN INITIATED**\n"
            "Banning all members...\n"
            "This will take time."
        )
        
        banned = failed = skipped = 0
        
        try:
            me = await client.get_me()
            targets = []
            
            # Collect all participants
            async for user in client.iter_participants(chat_id):
                if user.id == me.id:
                    continue  # Skip self
                if user.bot:
                    skipped += 1
                    continue  # Skip bots
                targets.append(user)
            
            total = len(targets)
            if not total:
                return await msg.edit("✅ No users to ban.")
            
            await msg.edit(f"🔥 **FUCKINGALLBYSHINU**\nFound {total} victims...")
            
            # Mass ban loop
            for idx, user in enumerate(targets, 1):
                name = user.username or user.first_name or str(user.id)
                
                success, _ = await safe_ban(client, chat_id, user.id, name)
                if success:
                    banned += 1
                else:
                    failed += 1
                
                # Update every 5
                if idx % 5 == 0:
                    try:
                        percent = (idx / total) * 100
                        await msg.edit(
                            f"🔥 **FUCKINGALLBYSHINU**\n"
                            f"Progress: {idx}/{total} ({percent:.0f}%)\n"
                            f"✅ Banned: {banned}\n"
                            f"❌ Failed: {failed}\n"
                            f"⏭️ Skipped: {skipped}"
                        )
                    except:
                        pass
                
                await asyncio.sleep(1.5)
                
        except Exception as e:
            logger.error(f"Mass ban error: {e}")
            await msg.edit(f"💥 Error: {e}")
            return
        
        # Final
        await msg.edit(
            f"🔥 **FUCKINGALLBYSHINU COMPLETE**\n\n"
            f"💀 Total Victims: {banned + failed}\n"
            f"✅ Banned: {banned}\n"
            f"❌ Failed: {failed}\n"
            f"🤖 Skipped (bots): {skipped}\n\n"
            f"Chat is now empty."
        )
    
    logger.info("Commands registered: .ban, .banall, .fuckingallbyshinu")


# Plugin loader
def load_banall(client):
    if not mark_plugin_loaded(client, "banall"):
        return

    register_commands(client)
    logger.info("✅ Ban plugin loaded")

load = load_banall
init = load_banall


# Standalone
if __name__ == "__main__":
    print("🚀 Ban Commands")
    print(".ban [user] - Single ban")
    print(".banall - Single ban (reply)")
    print(".fuckingallbyshinu - MASS BAN")
    print("=" * 40)
    
    client = TelegramClient("ban_session", API_ID, API_HASH)
    register_commands(client)
    client.start()
    print("✅ Ready!")
    client.run_until_disconnected()
