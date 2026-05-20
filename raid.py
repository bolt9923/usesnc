"""Compatibility wrapper.

The active Telethon auto-reply implementation lives in plugins/raid.py.
This file is kept so old imports like `import raid` do not crash the app.
"""

from plugins.raid import init, load, load_raid

__all__ = ["load_raid", "load", "init"]
