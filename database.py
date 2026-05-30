import aiosqlite

DB = "bot.db"

async def init():
    async with aiosqlite.connect(DB) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                full_name   TEXT,
                ref_code    TEXT UNIQUE,
                referred_by INTEGER,
                joined_at   TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS orders (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER,
                action     TEXT,
                crypto     TEXT,
                amount_uzs REAL,
                crypto_qty REAL,
                fee        REAL,
                status     TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS feedbacks (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER,
                message    TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS prices (
                crypto TEXT PRIMARY KEY,
                buy    REAL,
                sell   REAL
            );
        """)
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as c:
            return await c.fetchone()

async def create_user(user_id, username, full_name, ref_code, referred_by=None):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id,username,full_name,ref_code,referred_by) VALUES(?,?,?,?,?)",
            (user_id, username, full_name, ref_code, referred_by)
        )
        await db.commit()

async def get_user_by_ref(code):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE ref_code=?", (code,)) as c:
            return await c.fetchone()

async def get_referral_count(user_id):
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE referred_by=?", (user_id,)) as c:
            r = await c.fetchone()
            return r[0] if r else 0

async def add_order(user_id, action, crypto, amount_uzs, crypto_qty, fee):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT INTO orders (user_id,action,crypto,amount_uzs,crypto_qty,fee) VALUES(?,?,?,?,?,?)",
            (user_id, action, crypto, amount_uzs, crypto_qty, fee)
        )
        await db.commit()

async def get_orders(user_id, limit=5):
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        ) as c:
            return await c.fetchall()

async def add_feedback(user_id, message):
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT INTO feedbacks (user_id,message) VALUES(?,?)", (user_id, message))
        await db.commit()

async def get_prices():
    async with aiosqlite.connect(DB) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM prices") as c:
            rows = await c.fetchall()
            return {r["crypto"]: {"buy": r["buy"], "sell": r["sell"]} for r in rows}

async def set_price(crypto, buy, sell):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR REPLACE INTO prices (crypto,buy,sell) VALUES(?,?,?)",
            (crypto, buy, sell)
        )
        await db.commit()

async def get_stats():
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            users = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM orders") as c:
            orders = (await c.fetchone())[0]
        async with db.execute("SELECT SUM(fee) FROM orders") as c:
            fees = (await c.fetchone())[0] or 0
        return users, orders, fees

async def get_all_user_ids():
    async with aiosqlite.connect(DB) as db:
        async with db.execute("SELECT user_id FROM users") as c:
            return [r[0] for r in await c.fetchall()]
