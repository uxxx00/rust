import aiosqlite
import logging

log = logging.getLogger('database')

DB_PATH = 'rustplusbot.db'

async def init_db():
    log.info("Initializing database...")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS paired_devices (
                device_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                discord_id INTEGER PRIMARY KEY,
                steam_id TEXT UNIQUE NOT NULL,
                linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER,
                setting_key TEXT,
                setting_value TEXT,
                PRIMARY KEY (user_id, setting_key)
            )
        ''')
        await db.commit()
    log.info("Database initialized.")

async def add_device(device_id: int, name: str, device_type: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR REPLACE INTO paired_devices (device_id, name, type) VALUES (?, ?, ?)',
            (device_id, name, device_type)
        )
        await db.commit()

async def remove_device(device_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM paired_devices WHERE device_id = ?', (device_id,))
        await db.commit()

async def get_all_devices():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT device_id, name, type FROM paired_devices') as cursor:
            return await cursor.fetchall()

async def link_user(discord_id: int, steam_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR REPLACE INTO users (discord_id, steam_id) VALUES (?, ?)',
            (discord_id, steam_id)
        )
        await db.commit()

async def get_linked_user(discord_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT steam_id FROM users WHERE discord_id = ?', (discord_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
            (key, value)
        )
        await db.commit()

async def get_setting(key: str, default=None):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT value FROM settings WHERE key = ?', (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else default
