"""
╔══════════════════════════════════════════════════════════════════╗
║ OOREDOO BOT - by moon - VERSION 3.0.0 (ASYNC EDITION)            ║
║ ⚡ Async architecture — Handles 500+ concurrent users            ║
║ 🗄️ SQLite with WAL mode — 100x faster than JSON                  ║
║ 🔒 Per-user locks + asyncio.Semaphore                            ║
║ 🔁 Auto 429 retry — Smart rate limit handling                    ║
║ 🎁 2GB Gift (24h) → Manual Snake in app                          ║
╚══════════════════════════════════════════════════════════════════╝
"""

import asyncio
import base64
import json
import logging
import os
import re
import time
import urllib.parse
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

import aiosqlite
import httpx
import urllib3
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.error import TelegramError, RetryAfter, Forbidden, BadRequest
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════

BOT_TOKEN = "7792473952:AAEeacHzLmggmgl6Rs4C8fV6-FVq4F0gOyI"
ADMIN_IDS = {1726923679}
NOTIFY_CHANNEL_ID = "@by_moon_dz"

OOREDOO_BFF = "https://apis.ooredoo.dz/api/ooredoo-bff"
OOREDOO_AUTH = "https://apis.ooredoo.dz/api/auth/realms/myooredoo/protocol/openid-connect/token"
OOREDOO_CLIENT_ID = "myooredoo-app"
OOREDOO_X_VERSION = "1.5.17"
OOREDOO_X_SIG = "5c7641dbb82cf11066df68afc91541c967640106a95192740b43d51a5ce6777a"
OOREDOO_PLATFORM = "android"
OOREDOO_PLATFORM_ORIGIN = "mobile-android"

OOREDOO_INTEGRITY_1 = "JWBTpxXcH7KY9EXYeIRp8NjQMx2dt3vF8ejjoARazyoFzOw6Cu8+wkeV+zSVHSTeI6a12SG/FU+Q/9uBrcN71RlYO4CulD2x375NKwJRAInar8DVUilHBKUfjEsoHd6EwfLCfdYzLNXJu9POfEf6tqKn3PUe0pY6qZxWLhyVAFHw8Qwb52ZqdI2soCH4S3mrz+OZL+YovdGSUKlXKIkxVroAMTAg3jljLF7gvXaEsB/O3uW+tbkBMwSX2uTOwf+rh3sgOF/zPhKCFgRvZmU1o87Fa96Y/+wOcK+UpfXTCBYVrvQ1wG6ryC7vHMSqgUhYJK4tbSoti0zv4av9pwxh9Iv2MgsMENjyKBK/TuFZxEG3xQCKj1LTMgn2xBEeKcbsKrEW3xDRwsccGI3D7GHnbUlhdI4ujDIRQVKHaZSwhTp+32Cr4EB/Qt8p/xRbdgCde9MUlM4AYIGlfyVoHSkOvTu5c0DIIy1EhowtAkbKIJl49wsYKWvpT/nXFWzeXP3R2qzaclCnIb9qihhrarmwz8l8XH2T+f7AK2uSNiuWLG5Fy2mM/YLmuJPZT9Ciag/mpy7JGImKNQAcFbSAInBdKQjUKT+COzZfrXj5rwil9/HDMtuzIovq8hrQGY+roTfVPheTLWmcjkVCOL8VXAHjPb22vOuqrkMioWT9CQ5O8RgW7RKHrObeKQMp8F7tSjOqkxYDFkPVN1G4nkEBrTlPKK9YtPl+j7IuH9fGcDTwhCTTqP8peuBryW0L11tApvAEi7VkJyBxpVxW"
OOREDOO_INTEGRITY_2 = "JWBTpxXcH7KR/kzaHeUUydDWODuU4i3H4fL9gCgKzyYfyN4qLJJE8keV+zSVHSTeI6aEyC2tbSza/NGmkflQ/UgaNZSN9SKxz7tcdQckHY25n6mOaDZ9PPMQmF4sKZqDwebce/c1SNGNn6qvTULW/L348aJvy7Vii6dyPTu3OSPV9AwKwGwQKNHN61HyK3jx/fa8Os5ux9u3Q654YLZrAJ99QGEm/C9nEBPmlHC98RjovLGBnuJOGx6k7fnyrt/Ogy5fNg+tBgi5HEsoXDAwutX7TOWfx4YKHpKW//TvPRQgp69e2Xqa+CvGJJ+a/WlPMPhRCSsfo0OG04mVvlkc8eXiLzV/GPuJCEmcRf9Z6V+xoDyMtU7OZ3XT5BMhI/D/N68LsRn/9dIBH6X7n0WAW3tzeKZK1zENWFKrd7aLlzEdwFzO/1JTQsEDom5TRie0Kd5yic4BGvS1C1BsA2wJhzyiZ2j7RUE9m8tOAkPEIs929FYIfmH8XcCQKHT0TqT0+N+wCiyfNawPlDhZWcObscFZeEmKgvqiUFCoCj6xI1hvyHK0nu7fnZ/sGc6oNT/SrFjubYWjOyoYFL7gMnlYAhyjZhjuAwN1m1/wjwrOx8DbFr2NW8qb3hv+CIzK1zL3LDryKjqNkTxcOp4aJnmSTa73guCEmWc7pnLkLw5O8RgW7RKHrObeeQ0l9lu4HWXwlhdWRxvVMQDimhtTrGASL6sIuaxyhOkrH4HFImP70SaCoK9+euMxnzkPjg9HqPIFj+I0KSMloVxW"

OOREDOO_PROXIES = [
    "gate.busyip.com:18080:bi_23ee2cd9-session-s1-type-residential-mode-sticky:9C0h1L16DX5gwKbv",
]

DB_PATH = "ooredoo.db"
MAX_NUMBERS_PER_USER = 3
GIFT_2GB_COOLDOWN = 24 * 3600

# ⚡ التزامن — تحكم في عدد الطلبات الخارجية المتزامنة
MAX_CONCURRENT_OOREDOO = 50   # حد أقصى 50 طلب أوريدو متزامن
MAX_CONCURRENT_TG = 25         # حد أقصى 25 رسالة تيليجرام متزامنة

ooredoo_semaphore = asyncio.Semaphore(MAX_CONCURRENT_OOREDOO)
tg_semaphore = asyncio.Semaphore(MAX_CONCURRENT_TG)

# 🔐 أقفال per-user لمنع race conditions
user_locks: Dict[int, asyncio.Lock] = {}
_lock_guard = asyncio.Lock()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("moon_bot")

LINE        = "━━━━━━━━━━━━━━━━━━━━━━"
LINE_LIGHT  = "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"
DOT         = "▸"
DIAMOND     = "◈"
CIRCLE      = "●"


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _box(content):
    return f"<code>  {content}  </code>"


async def get_user_lock(chat_id: int) -> asyncio.Lock:
    """جلب/إنشاء قفل خاص بالمستخدم لمنع race conditions"""
    async with _lock_guard:
        if chat_id not in user_locks:
            user_locks[chat_id] = asyncio.Lock()
        return user_locks[chat_id]


def mask_msisdn(msisdn):
    if not msisdn or len(msisdn) < 4: return "********"
    return msisdn[:2] + "*" * (len(msisdn) - 4) + msisdn[-2:]


def normalize_msisdn(text):
    digits = "".join(c for c in text if c.isdigit())
    if len(digits) == 10 and digits.startswith("0"):
        return "213" + digits[1:]
    if len(digits) == 12 and digits.startswith("213"):
        return digits
    return None


def is_valid_ooredoo_number(text):
    if not text: return False
    text = re.sub(r'[\s\(\)\-]', '', text.strip())
    return bool(re.match(r'^05\d{8}$', text))


def is_admin(chat_id: int) -> bool:
    return chat_id in ADMIN_IDS


def format_duration(seconds):
    if seconds <= 0: return "الآن"
    d = seconds // 86400
    h = (seconds % 86400) // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    parts = []
    if d > 0: parts.append(f"{d} يوم")
    if h > 0: parts.append(f"{h} ساعة")
    if m > 0: parts.append(f"{m} دقيقة")
    if s > 0 and d == 0 and h == 0: parts.append(f"{s} ثانية")
    return " و ".join(parts) if parts else "الآن"


def ooredoo_now_ms(): return str(int(time.time() * 1000))
def ooredoo_new_instance_id():
    u = uuid.uuid4().hex
    return f"{u[:8]}-{u[8:12]}-11{u[12:16]}-{u[16:20]}-{u[20:32]}{ooredoo_now_ms()}"
def ooredoo_new_plat_sig(iid):
    p = json.dumps({"platform": "android", "is-physical-device": True, "device-id": iid}, separators=(',', ':'))
    return base64.b64encode(p.encode()).decode()
def ooredoo_new_corr_id(): return uuid.uuid4().hex + ooredoo_now_ms()
def ooredoo_new_fingerprint(): return uuid.uuid4().hex + uuid.uuid4().hex[:32]


def ooredoo_parse_proxy(raw):
    try:
        if not raw or not isinstance(raw, str): return None
        p = raw.strip().split(":", 3)
        if len(p) >= 4: return {"host": f"{p[0]}:{p[1]}", "userpass": f"{p[2]}:{p[3]}"}
        elif len(p) == 2: return {"host": f"{p[0]}:{p[1]}", "userpass": ""}
    except: pass
    return None


def get_valid_proxies():
    return [ooredoo_parse_proxy(p) for p in OOREDOO_PROXIES if ooredoo_parse_proxy(p)]


# ═══════════════════════════════════════════════════════════════
# SQLITE DATABASE (WAL mode — thread-safe + fast)
# ═══════════════════════════════════════════════════════════════

_db_ready = False

async def init_db():
    """إنشاء الجداول + WAL mode للسرعة القصوى"""
    global _db_ready
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL")
        await db.execute("PRAGMA cache_size=-64000")
        await db.execute("PRAGMA temp_store=MEMORY")

        # المستخدمون
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                msisdn TEXT,
                msisdns TEXT,
                numbers_data TEXT,
                last_2gb_claim TEXT,
                last_activation_at INTEGER DEFAULT 0,
                created_at INTEGER
            )
        """)

        # الإعدادات
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # البريميوم
        await db.execute("""
            CREATE TABLE IF NOT EXISTS premium (
                msisdn TEXT PRIMARY KEY,
                added_by INTEGER,
                added_at INTEGER,
                note TEXT
            )
        """)

        # الإحصائيات
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                key TEXT PRIMARY KEY,
                value INTEGER DEFAULT 0
            )
        """)

        # القنوات
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                chat_id TEXT PRIMARY KEY,
                title TEXT
            )
        """)

        # فهارس للأداء
        await db.execute("CREATE INDEX IF NOT EXISTS idx_msisdn ON users(msisdn)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_premium ON premium(msisdn)")

        # القيم الافتراضية
        await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('cooldown_mode', 'unlimited')")
        await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('cooldown_hours', '0')")
        await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('force_join_enabled', 'false')")
        await db.execute("INSERT OR IGNORE INTO stats (key, value) VALUES ('total_users', 0)")
        await db.execute("INSERT OR IGNORE INTO stats (key, value) VALUES ('total_activations', 0)")
        await db.execute("INSERT OR IGNORE INTO stats (key, value) VALUES ('total_2gb_claims', 0)")
        await db.execute("INSERT OR IGNORE INTO stats (key, value) VALUES ('started_at', ?)", (int(time.time()),))

        await db.commit()
    _db_ready = True
    logger.info("✅ Database initialized (WAL mode)")


# ═══════════════════════════════════════════════════════════════
# DB HELPERS — المستخدمون
# ═══════════════════════════════════════════════════════════════

async def db_get_user(chat_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,)) as cur:
            row = await cur.fetchone()
            if not row: return None
            return {
                "chat_id": row["chat_id"],
                "msisdn": row["msisdn"],
                "msisdns": json.loads(row["msisdns"] or "[]"),
                "numbers_data": json.loads(row["numbers_data"] or "{}"),
                "last_2gb_claim": json.loads(row["last_2gb_claim"] or "{}"),
                "last_activation_at": row["last_activation_at"] or 0,
                "created_at": row["created_at"] or int(time.time()),
            }


async def db_save_user(chat_id: int, data: Dict[str, Any]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (chat_id, msisdn, msisdns, numbers_data, last_2gb_claim, last_activation_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                msisdn=excluded.msisdn,
                msisdns=excluded.msisdns,
                numbers_data=excluded.numbers_data,
                last_2gb_claim=excluded.last_2gb_claim,
                last_activation_at=excluded.last_activation_at
        """, (
            chat_id,
            data.get("msisdn"),
            json.dumps(data.get("msisdns", [])),
            json.dumps(data.get("numbers_data", {})),
            json.dumps(data.get("last_2gb_claim", {})),
            data.get("last_activation_at", 0),
            data.get("created_at", int(time.time())),
        ))
        await db.commit()


async def db_delete_user(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users WHERE chat_id = ?", (chat_id,))
        await db.commit()


async def db_count_users() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


async def db_find_owner_of_msisdn(msisdn: str) -> Optional[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT chat_id, msisdns FROM users") as cur:
            async for row in cur:
                try:
                    nums = json.loads(row[1] or "[]")
                    if msisdn in nums:
                        return row[0]
                except: pass
    return None


# ═══════════════════════════════════════════════════════════════
# DB HELPERS — الإعدادات
# ═══════════════════════════════════════════════════════════════

async def db_get_setting(key: str, default=None):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else default


async def db_set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        await db.commit()


async def db_get_cooldown_seconds() -> int:
    mode = await db_get_setting("cooldown_mode", "unlimited")
    if mode == "unlimited": return 0
    hours = int(await db_get_setting("cooldown_hours", "0") or 0)
    return hours * 3600


async def db_is_force_join_enabled() -> bool:
    val = await db_get_setting("force_join_enabled", "false")
    return val == "true"


# ═══════════════════════════════════════════════════════════════
# DB HELPERS — البريميوم
# ═══════════════════════════════════════════════════════════════

async def db_is_premium(msisdn: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM premium WHERE msisdn = ?", (msisdn,)) as cur:
            return await cur.fetchone() is not None


async def db_add_premium(msisdn: str, added_by: int, note: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO premium (msisdn, added_by, added_at, note) VALUES (?, ?, ?, ?)",
            (msisdn, added_by, int(time.time()), note),
        )
        await db.commit()


async def db_remove_premium(msisdn: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM premium WHERE msisdn = ?", (msisdn,))
        await db.commit()
        return cur.rowcount > 0


async def db_count_premium() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM premium") as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


# ═══════════════════════════════════════════════════════════════
# DB HELPERS — الإحصائيات
# ═══════════════════════════════════════════════════════════════

async def db_inc_stat(key: str, amount: int = 1):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO stats (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = value + ?",
            (key, amount, amount),
        )
        await db.commit()


async def db_get_stat(key: str, default: int = 0) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM stats WHERE key = ?", (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else default


# ═══════════════════════════════════════════════════════════════
# DB HELPERS — القنوات
# ═══════════════════════════════════════════════════════════════

async def db_get_channels():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT chat_id, title FROM channels") as cur:
            return [{"chat_id": row[0], "title": row[1]} async for row in cur]


async def db_add_channel(chat_id: str, title: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("INSERT INTO channels (chat_id, title) VALUES (?, ?)", (chat_id, title))
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def db_remove_channel(chat_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM channels WHERE chat_id = ?", (chat_id,))
        await db.commit()
        return cur.rowcount > 0


# ═══════════════════════════════════════════════════════════════
# HTTP CLIENT (Async)
# ═══════════════════════════════════════════════════════════════

http_client: Optional[httpx.AsyncClient] = None

def get_http_client() -> httpx.AsyncClient:
    global http_client
    if http_client is None:
        http_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=200,
                max_keepalive_connections=100,
                keepalive_expiry=30.0,
            ),
            timeout=httpx.Timeout(10.0, connect=5.0),
            verify=False,
            http2=False,
            follow_redirects=False,
        )
    return http_client


async def close_http_client():
    global http_client
    if http_client:
        await http_client.aclose()
        http_client = None


async def _ooredoo_do_request(method, url, headers, body="", proxy=None, timeout=10):
    proxy_url = None
    if proxy and proxy.get("host"):
        if proxy.get("userpass"):
            proxy_url = f"http://{proxy['userpass']}@{proxy['host']}"
        else:
            proxy_url = f"http://{proxy['host']}"
    try:
        client = get_http_client()
        req_kwargs = {"headers": headers, "timeout": timeout}
        if proxy_url:
            req_kwargs["proxy"] = proxy_url
        if method == "GET":
            r = await client.get(url, **req_kwargs)
        elif method == "HEAD":
            r = await client.head(url, **req_kwargs)
        else:
            req_kwargs["content"] = body
            r = await client.post(url, **req_kwargs)
        txt = r.text
        if "<!DOCTYPE" in txt or "<html" in txt:
            return {"ip_blocked": True, "code": r.status_code}
        try: j = r.json()
        except: j = None
        return {"code": r.status_code, "body": txt, "headers": {k.lower(): v for k, v in r.headers.items()}, "json": j}
    except Exception as e:
        logger.debug(f"HTTP error: {e}")
        return None


async def ooredoo_http_request(method, url, headers, body="", proxy=None, timeout=10):
    async with ooredoo_semaphore:
        result = await _ooredoo_do_request(method, url, headers, body, proxy, timeout)
        if result is None and proxy is not None:
            result = await _ooredoo_do_request(method, url, headers, body, None, timeout)
        return result


# ═══════════════════════════════════════════════════════════════
# HEADERS
# ═══════════════════════════════════════════════════════════════

def ooredoo_base_headers(msisdn, fp, corr, ts, iid, psig):
    return {"User-Agent": "Dart/3.11 (dart:io)", "Accept-Encoding": "gzip", "x-msisdn": msisdn,
            "x-device-fingerprint": fp, "x-platform-origin": OOREDOO_PLATFORM_ORIGIN,
            "x-correlation-id": corr, "platform": OOREDOO_PLATFORM, "x-version": OOREDOO_X_VERSION,
            "x-signature": OOREDOO_X_SIG, "x-platform-data-signature": psig,
            "x-timestamp": ts, "x-instance-id": iid}


def ooredoo_authed_headers_web(msisdn, token, tok_hdrs):
    ts = tok_hdrs.get("tok_timestamp") or ooredoo_now_ms()
    iid = tok_hdrs.get("tok_instance_id") or ooredoo_new_instance_id()
    psig = tok_hdrs.get("tok_plat_sig") or ooredoo_new_plat_sig(iid)
    return {"User-Agent": "Dart/3.11 (dart:io)", "Accept-Encoding": "gzip", "x-msisdn": msisdn,
            "x-device-fingerprint": ooredoo_new_fingerprint(), "x-platform-origin": "web",
            "authorization": f"Bearer {token}", "x-correlation-id": ooredoo_new_corr_id(),
            "platform": "web", "x-version": OOREDOO_X_VERSION, "x-signature": OOREDOO_X_SIG,
            "x-platform-data-signature": psig, "x-timestamp": ts, "x-instance-id": iid,
            "origin": "https://my.ooredoo.dz", "referer": "https://my.ooredoo.dz/"}


def ooredoo_token_proxy(user):
    host = user.get("token_proxy_host", "direct")
    up = user.get("token_proxy_user", "")
    if host == "direct" or not host: return None
    return {"host": host, "userpass": up}


def ooredoo_tok_hdrs(user):
    return {"tok_timestamp": user.get("tok_timestamp"), "tok_instance_id": user.get("tok_instance_id"),
            "tok_plat_sig": user.get("tok_plat_sig")}


# ═══════════════════════════════════════════════════════════════
# OTP + Verify
# ═══════════════════════════════════════════════════════════════

async def ooredoo_send_otp(msisdn, device, max_attempts=4):
    iid = device["instance_id"]
    psig = device["plat_sig"]
    all_proxies = get_valid_proxies() + [None]
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"📲 OTP attempt {attempt}/{max_attempts}")
            for proxy in all_proxies:
                ts, corr = ooredoo_now_ms(), ooredoo_new_corr_id()
                h1 = ooredoo_base_headers(msisdn, ooredoo_new_fingerprint(), corr, ts, iid, psig)
                r1 = await ooredoo_http_request("GET", f"{OOREDOO_BFF}/users/status?msisdn={msisdn}", h1, proxy=proxy, timeout=6)
                if not r1 or r1.get("ip_blocked") or r1.get("code") != 200: continue
                h2 = ooredoo_base_headers(msisdn, ooredoo_new_fingerprint(), ooredoo_new_corr_id(), ooredoo_now_ms(), iid, psig)
                r2 = await ooredoo_http_request("HEAD", f"{OOREDOO_BFF}/userInfo?msisdn={msisdn}", h2, proxy=proxy, timeout=6)
                if not r2 or r2.get("ip_blocked") or r2.get("code") not in (200, 204): continue
                for p34 in all_proxies:
                    ts = ooredoo_now_ms(); corr = ooredoo_new_corr_id()
                    h3 = ooredoo_base_headers(msisdn, ooredoo_new_fingerprint(), corr, ts, iid, psig)
                    h3["content-type"] = "application/json; charset=utf-8"
                    h3["x-native-integrity-token"] = OOREDOO_INTEGRITY_1
                    h3["x-path"] = "/api/auth/realms/myooredoo/protocol/openid-connect/token"
                    h3["x-method"] = "POST"
                    r3 = await ooredoo_http_request("POST", f"{OOREDOO_BFF}/checkpoint/token", h3, body="{}", proxy=p34, timeout=6)
                    if not r3 or r3.get("ip_blocked"): continue
                    nonce = r3.get("headers", {}).get("x-nonce-id")
                    chronos = r3.get("headers", {}).get("x-chronos-id")
                    if not nonce or not chronos: continue
                    h4 = {"User-Agent": "Dart/3.11 (dart:io)", "Accept-Encoding": "gzip", "x-msisdn": msisdn,
                          "x-device-fingerprint": ooredoo_new_fingerprint(), "x-nonce-id": nonce,
                          "x-platform-origin": OOREDOO_PLATFORM_ORIGIN, "platform": OOREDOO_PLATFORM,
                          "x-version": OOREDOO_X_VERSION, "x-signature": OOREDOO_X_SIG,
                          "x-chronos-id": chronos, "x-timestamp": ts, "x-platform-info": psig,
                          "x-force-update": "true", "x-instance-id": iid,
                          "Content-Type": "application/x-www-form-urlencoded"}
                    body4 = urllib.parse.urlencode({"client_id": OOREDOO_CLIENT_ID, "grant_type": "password", "username": msisdn})
                    r4 = await ooredoo_http_request("POST", OOREDOO_AUTH, h4, body=body4, proxy=p34, timeout=8)
                    if r4 and r4.get("code") in (401, 403):
                        logger.info(f"✅ OTP sent (attempt {attempt})")
                        return {"proxy": p34}
            if attempt < max_attempts:
                await asyncio.sleep(2 * attempt)
        except Exception as e:
            logger.warning(f"OTP attempt {attempt} error: {e}")
            if attempt < max_attempts:
                await asyncio.sleep(2 * attempt)
    return None


async def ooredoo_verify_otp(msisdn, otp, proxy, device):
    try:
        iid = device["instance_id"]; psig = device["plat_sig"]
        ts = ooredoo_now_ms(); corr = ooredoo_new_corr_id()
        h6 = ooredoo_base_headers(msisdn, ooredoo_new_fingerprint(), corr, ts, iid, psig)
        h6["content-type"] = "application/json; charset=utf-8"
        h6["x-native-integrity-token"] = OOREDOO_INTEGRITY_2
        h6["x-path"] = "/api/auth/realms/myooredoo/protocol/openid-connect/token"
        h6["x-method"] = "POST"
        r6 = await ooredoo_http_request("POST", f"{OOREDOO_BFF}/checkpoint/token", h6, body="{}", proxy=proxy, timeout=6)
        if not r6 or r6.get("ip_blocked"): return None
        nonce2 = r6.get("headers", {}).get("x-nonce-id")
        chronos2 = r6.get("headers", {}).get("x-chronos-id")
        if not nonce2 or not chronos2: return None
        fp7 = ooredoo_new_fingerprint()
        h7 = {"User-Agent": "Dart/3.11 (dart:io)", "Accept-Encoding": "gzip", "x-msisdn": msisdn,
              "x-device-fingerprint": fp7, "x-nonce-id": nonce2, "x-platform-origin": OOREDOO_PLATFORM_ORIGIN,
              "platform": OOREDOO_PLATFORM, "x-version": OOREDOO_X_VERSION, "x-signature": OOREDOO_X_SIG,
              "x-chronos-id": chronos2, "x-timestamp": ts, "x-platform-info": psig,
              "x-force-update": "true", "x-instance-id": iid, "Content-Type": "application/x-www-form-urlencoded"}
        body7 = urllib.parse.urlencode({"client_id": OOREDOO_CLIENT_ID, "grant_type": "password", "username": msisdn, "otp": otp})
        r7 = await ooredoo_http_request("POST", OOREDOO_AUTH, h7, body=body7, proxy=proxy, timeout=8)
        if not r7: return None
        if r7.get("code") in (401, 403): return "wrong_otp"
        if r7.get("code") == 200 and r7.get("json") and "access_token" in r7["json"]:
            j = r7["json"]
            return {"access_token": j["access_token"], "refresh_token": j.get("refresh_token", ""),
                    "token_proxy_host": proxy["host"] if proxy else "direct",
                    "token_proxy_user": proxy["userpass"] if proxy else "",
                    "tok_fingerprint": fp7, "tok_timestamp": ts, "tok_instance_id": iid,
                    "tok_plat_sig": psig, "tok_correlation": corr}
    except Exception as e:
        logger.warning(f"Verify error: {e}")
    return None


async def ooredoo_refresh_token(msisdn, user, device):
    try:
        rt = user.get("refresh_token", "")
        if not rt: return "expired"
        iid = device["instance_id"]; psig = device["plat_sig"]; ts = ooredoo_now_ms()
        h = {"User-Agent": "Dart/3.11 (dart:io)", "Accept-Encoding": "gzip",
             "Content-Type": "application/x-www-form-urlencoded", "x-msisdn": msisdn,
             "x-platform-origin": OOREDOO_PLATFORM_ORIGIN, "platform": OOREDOO_PLATFORM,
             "x-version": OOREDOO_X_VERSION, "x-signature": OOREDOO_X_SIG,
             "x-platform-data-signature": psig, "x-timestamp": ts, "x-instance-id": iid}
        body = urllib.parse.urlencode({"client_id": OOREDOO_CLIENT_ID, "grant_type": "refresh_token", "refresh_token": rt})
        r = await ooredoo_http_request("POST", OOREDOO_AUTH, h, body=body, proxy=ooredoo_token_proxy(user), timeout=8)
        if not r: return False
        if r.get("code") == 400 and (r.get("json") or {}).get("error") == "invalid_grant": return "expired"
        if r.get("code") == 200 and r.get("json") and "access_token" in r["json"]:
            j = r["json"]
            return {"access_token": j["access_token"], "refresh_token": j.get("refresh_token", rt),
                    "token_proxy_host": user.get("token_proxy_host", "direct"),
                    "token_proxy_user": user.get("token_proxy_user", ""),
                    "tok_fingerprint": ooredoo_new_fingerprint(), "tok_timestamp": ts,
                    "tok_instance_id": iid, "tok_plat_sig": psig, "tok_correlation": ooredoo_new_corr_id()}
    except: pass
    return False


# ═══════════════════════════════════════════════════════════════
# تسجيل 2GB
# ═══════════════════════════════════════════════════════════════

async def ooredoo_claim_2gb_gift(msisdn, user_data):
    try:
        token = user_data.get("access_token")
        if not token:
            return {"success": False, "already_claimed": False, "message": "no_token"}

        tok_hdrs = {
            "tok_timestamp": user_data.get("tok_timestamp"),
            "tok_instance_id": user_data.get("tok_instance_id"),
            "tok_plat_sig": user_data.get("tok_plat_sig"),
        }
        headers = ooredoo_authed_headers_web(msisdn, token, tok_hdrs)
        headers["content-type"] = "application/json; charset=utf-8"
        headers["accept"] = "*/*"

        body = json.dumps({"bundleCode": "BTL_24H_DATA_Free_2Go"})

        proxy = None
        if user_data.get("token_proxy_host") and user_data.get("token_proxy_host") != "direct":
            proxy = {"host": user_data.get("token_proxy_host"),
                     "userpass": user_data.get("token_proxy_user", "")}

        res = await ooredoo_http_request(
            "POST",
            f"{OOREDOO_BFF}/cvm/dynamic-bundle-purchase",
            headers, body=body, proxy=proxy, timeout=15,
        )

        if res and res.get("code") == 401:
            device = {"instance_id": ooredoo_new_instance_id(), "plat_sig": user_data.get("tok_plat_sig", "")}
            new_tok = await ooredoo_refresh_token(msisdn, user_data, device)
            if isinstance(new_tok, dict):
                user_data.update(new_tok)
                return await ooredoo_claim_2gb_gift(msisdn, user_data)

        if not res:
            return {"success": False, "already_claimed": False, "message": "connection_error"}

        if res.get("code") == 200:
            return {"success": True, "already_claimed": False, "message": "ok"}

        body_lower = (res.get("body") or "").lower()
        if res.get("code") in (400, 403, 409, 429) or any(
            kw in body_lower for kw in ("already", "exist", "limit", "24", "consume", "used")
        ):
            return {"success": False, "already_claimed": True, "message": "already"}

        return {"success": False, "already_claimed": False, "message": f"HTTP {res.get('code')}"}

    except Exception as e:
        logger.error(f"claim 2gb error: {e}")
        return {"success": False, "already_claimed": False, "message": str(e)}


# ═══════════════════════════════════════════════════════════════
# حالة المستخدم (session)
# ═══════════════════════════════════════════════════════════════

sessions: Dict[int, Dict[str, Any]] = {}
devices: Dict[int, Dict[str, Any]] = {}
otp_cooldown: Dict[str, float] = {}
admin_states: Dict[int, Dict[str, Any]] = {}


def get_session(chat_id): return sessions.get(chat_id, {})
def set_session(chat_id, data): sessions[chat_id] = data
def clear_session(chat_id): sessions.pop(chat_id, None)

def get_device(chat_id):
    if chat_id not in devices:
        iid = ooredoo_new_instance_id()
        devices[chat_id] = {"instance_id": iid, "plat_sig": ooredoo_new_plat_sig(iid)}
    return devices[chat_id]


# ═══════════════════════════════════════════════════════════════
# Telegram SEND (with 429 retry)
# ═══════════════════════════════════════════════════════════════

async def safe_send(context, chat_id, text, reply_markup=None, parse_mode=ParseMode.HTML):
    """إرسال رسالة مع retry تلقائي على 429"""
    async with tg_semaphore:
        for attempt in range(3):
            try:
                return await context.bot.send_message(
                    chat_id=chat_id, text=text,
                    reply_markup=reply_markup, parse_mode=parse_mode,
                )
            except RetryAfter as e:
                wait = e.retry_after
                logger.warning(f"429 on send to {chat_id}, waiting {wait}s")
                await asyncio.sleep(wait)
            except (Forbidden, BadRequest) as e:
                logger.warning(f"Send error to {chat_id}: {e}")
                return None
            except TelegramError as e:
                logger.error(f"Telegram error: {e}")
                if attempt < 2:
                    await asyncio.sleep(1)
                else:
                    return None
    return None


async def safe_edit(context, chat_id, message_id, text, reply_markup=None, parse_mode=ParseMode.HTML):
    async with tg_semaphore:
        for attempt in range(3):
            try:
                return await context.bot.edit_message_text(
                    chat_id=chat_id, message_id=message_id, text=text,
                    reply_markup=reply_markup, parse_mode=parse_mode,
                )
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after)
            except BadRequest as e:
                # edit may fail if message unchanged
                if "message is not modified" in str(e).lower():
                    return None
                logger.debug(f"Edit error: {e}")
                return None
            except TelegramError as e:
                logger.error(f"Edit telegram error: {e}")
                return None
    return None


# ═══════════════════════════════════════════════════════════════
# TEXT BUILDERS
# ═══════════════════════════════════════════════════════════════

def fmt_welcome():
    return (
        f"╭━━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"   <b>💜 بوت أوريدو</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"{DIAMOND} <i>هدية 2GB + هدية Snake مجاناً</i>\n"
        f"{DIAMOND} <i>تفعيل سهل وسريع</i>\n"
        f"{DIAMOND} <i>متاح كل 24 ساعة</i>\n\n"
        f"{LINE}\n\n"
        f"📱 <b>أرسل رقم هاتفك</b>\n"
        f"{DOT} 10 أرقام تبدأ بـ <code>05</code>\n\n"
        f"╭─────────────────────╮\n"
        f"  <code>05 XX XX XX XX</code>\n"
        f"╰─────────────────────╯"
    )


def fmt_welcome_back_multi(user):
    nums = user.get("msisdns", [])
    lines = [
        f"╭━━━━━━━━━━━━━━━━━━━━━━╮",
        f"   <b>💜 مرحباً بعودتك</b>",
        f"╰━━━━━━━━━━━━━━━━━━━━━━╯",
        f"",
        f"📱 <b>أرقامك المسجلة ({len(nums)}/{MAX_NUMBERS_PER_USER}):</b>",
        f"",
    ]
    for i, m in enumerate(nums, 1):
        lines.append(f"  {i}. <code>{mask_msisdn(m)}</code>")
    lines.append("")
    lines.append(f"{LINE}")
    lines.append("")
    lines.append(f"🎁 <i>اضغط</i> <b>تفعيل هدية 2GB</b> <i>للبدء</i>")
    lines.append(f"🐍 <i>ستحصل على هدية Snake مجانية</i>")
    return "\n".join(lines)


def fmt_add_number():
    return (
        f"╭━━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"   <b>➕ إضافة رقم آخر</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"📱 <b>أرسل رقمك الآن</b>\n"
        f"{DOT} 10 أرقام تبدأ بـ <code>05</code>\n\n"
        f"{LINE_LIGHT}\n\n"
        f"⚡ <b>رقم محفوظ</b> → <i>تفعيل تلقائي فوري</i>\n"
        f"📲 <b>رقم جديد</b> → <i>إرسال رمز تحقق</i>\n\n"
        f"{LINE_LIGHT}\n"
        f"⚠️ <b>ملاحظة:</b> <i>لا يمكن تسجيل رقم مستخدم آخر</i>"
    )


def fmt_relogin():
    return (
        f"╭━━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"   <b>🔄 تم تسجيل الخروج</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"📱 <b>أرسل رقمك لبدء التفعيل</b>\n"
        f"{_box('05 XX XX XX XX')}"
    )


def fmt_login_success(masked):
    return (
        f"╭━━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"   <b>🎉 تم الربط بنجاح</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"📱 <b>الرقم المرتبط:</b>\n"
        f"{_box(masked)}\n\n"
        f"{LINE}\n\n"
        f"✨ <i>اختر ما تحتاجه 👇</i>"
    )


def fmt_otp_sending():
    return (
        f"📤 <b>جاري إرسال رمز التحقق</b>\n"
        f"{LINE_LIGHT}\n"
        f"{CIRCLE} <i>قد يستغرق الأمر بضع ثوانٍ</i>\n"
        f"{CIRCLE} <i>حتى 4 محاولات تلقائية</i>"
    )


def fmt_otp_sent():
    return (
        f"╭━━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"   <b>✅ تم إرسال الرمز</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"📲 <b>أدخل الرمز المكوّن من 6 أرقام</b>\n\n"
        f"{LINE_LIGHT}\n"
        f"💡 <i>تحقق من رسائلك النصية</i>"
    )


def fmt_otp_verifying():
    return f"🔐 <b>جاري التحقق من الرمز...</b>\n{LINE_LIGHT}\n{CIRCLE} <i>لحظات من فضلك</i>"


def fmt_otp_wrong():
    return f"❌ <b>رمز التحقق غير صحيح</b>\n{LINE_LIGHT}\n🔁 <i>يرجى المحاولة مرة أخرى</i>"


def fmt_otp_failed():
    return (
        f"❌ <b>فشل إرسال رمز التحقق</b>\n"
        f"{LINE_LIGHT}\n"
        f"{CIRCLE} <i>تمت 4 محاولات دون نجاح</i>\n"
        f"{CIRCLE} <i>يرجى إعادة المحاولة لاحقاً</i>"
    )


def fmt_otp_invalid():
    return f"❌ <b>صيغة الرمز غير صحيحة</b>\n{LINE_LIGHT}\n📲 <i>يجب أن يكون 6 أرقام</i>"


def fmt_invalid_number():
    return (
        f"❌ <b>رقم غير صحيح</b>\n"
        f"{LINE_LIGHT}\n"
        f"📱 <b>أرسل رقم أوريدو صحيح:</b>\n"
        f"{_box('05 XX XX XX XX')}"
    )


def fmt_cooldown(seconds):
    return f"⏳ <b>يرجى الانتظار</b>\n{LINE_LIGHT}\n⏱️ <b>{seconds} ثانية</b> <i>قبل طلب رمز جديد</i>"


def fmt_2gb_start():
    return (
        f"╭━━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"   <b>🎁 جاري تسجيل هدية 2GB</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"{CIRCLE} <b>الهدية:</b> <code>2 GB / 24h</code>\n"
        f"{CIRCLE} <i>يرجى الانتظار...</i>\n\n"
        f"{LINE_LIGHT}\n\n"
        f"<i>⏳ جاري الاتصال بأوريدو</i>"
    )


def fmt_2gb_wait(remaining):
    return (
        f"╭━━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"   <b>⏳ انتظر 24 ساعة</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"🔒 <b>هدية 2GB مسجلة مسبقاً</b>\n\n"
        f"{LINE}\n\n"
        f"⏱️ <b>المتبقي:</b>\n"
        f"{_box(format_duration(remaining))}\n\n"
        f"{LINE_LIGHT}\n"
        f"💡 <i>هذه الهدية متاحة كل 24 ساعة</i>"
    )


def fmt_2gb_error():
    return (
        f"╭━━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"   <b>❌ فشل تسجيل هدية 2GB</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"{LINE_LIGHT}\n\n"
        f"🔁 <i>يرجى إعادة المحاولة لاحقاً</i>"
    )


def fmt_2gb_success(msisdn):
    return (
        f"╭━━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"   <b>🎉 تم تفعيل هديتك</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"📱 <b>الرقم:</b> <code>{mask_msisdn(msisdn)}</code>\n\n"
        f"{LINE}\n\n"
        f"<b>✅ تم تسجيل هدية 2GB</b>\n"
        f"<b>🐍 وحصلت على هدية Snake مجانية واحدة</b>\n\n"
        f"{LINE}\n\n"
        f"📱 <b>لفتح هدية Snake:</b>\n\n"
        f"  <b>1.</b> {DOT} <i>ادخل إلى تطبيق</i> <b>My Ooredoo</b>\n"
        f"  <b>2.</b> {DOT} <i>اذهب إلى قسم</i> <b>Power Snake</b> 🐍\n"
        f"  <b>3.</b> {DOT} <i>افتح هديتك</i> 🎁\n\n"
        f"{LINE_LIGHT}\n\n"
        f"💡 <i>الهدية متاحة كل 24 ساعة</i>\n\n"
        f"<i>⚡ by moon</i>"
    )


def fmt_limit_reached():
    return (
        f"╭━━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"   <b>⛔ الحد الأقصى</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"🔒 <b>لقد وصلت للحد الأقصى</b>\n"
        f"📱 <b>3 أرقام</b> لكل مستخدم\n\n"
        f"{LINE_LIGHT}\n\n"
        f"💡 <i>يمكنك استخدام رقم موجود</i>\n"
        f"🔄 <i>أو تسجيل الخروج من جديد</i>"
    )


def fmt_number_taken(masked):
    return (
        f"╭━━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"   <b>⛔ الرقم محجوز</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"📱 <b>الرقم:</b> <code>{masked}</code>\n\n"
        f"{LINE_LIGHT}\n\n"
        f"⚠️ <b>هذا الرقم مسجل من طرف</b>\n"
        f"<b>مستخدم آخر مسبقاً</b>\n\n"
        f"🔁 <i>يرجى استخدام رقم آخر</i>"
    )


def fmt_join_required(missing):
    lines = [
        f"╭━━━━━━━━━━━━━━━━━━━━━━╮",
        f"   <b>🔒 اشتراك مطلوب</b>",
        f"╰━━━━━━━━━━━━━━━━━━━━━━╯",
        f"",
        f"<i>للاستمرار، يجب الاشتراك في:</i>",
        f"",
        f"{LINE}",
        f"",
    ]
    for i, c in enumerate(missing, 1):
        lines.append(f"  {i}. {c.get('title') or c['chat_id']}")
    lines.append("")
    lines.append(f"{LINE_LIGHT}")
    lines.append("")
    lines.append(f"✅ <i>بعد الاشتراك اضغط</i> <b>تحقق</b>")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# KEYBOARDS
# ═══════════════════════════════════════════════════════════════

def kb_main(chat_id, num_count):
    buttons = [
        [InlineKeyboardButton("🎁 تفعيل هدية 2GB", callback_data="menu_claim_2gb")],
    ]
    if num_count < MAX_NUMBERS_PER_USER:
        buttons.append([InlineKeyboardButton("➕ إضافة رقم آخر", callback_data="menu_add_number")])
    buttons.append([InlineKeyboardButton("🔄 تسجيل الدخول من جديد", callback_data="menu_relogin")])
    if is_admin(chat_id):
        buttons.append([InlineKeyboardButton("👑 لوحة الأدمن", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)


def kb_admin():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
         InlineKeyboardButton("⏱️ وقت الانتظار", callback_data="admin_cooldown")],
        [InlineKeyboardButton("⭐ البريميوم", callback_data="admin_premium"),
         InlineKeyboardButton("🔐 الاشتراك الإجباري", callback_data="admin_force_join")],
        [InlineKeyboardButton("📢 إذاعة رسالة", callback_data="admin_broadcast"),
         InlineKeyboardButton("🗑️ محو البيانات", callback_data="admin_reset")],
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="admin_back_main")],
    ])


def kb_join(missing):
    buttons = []
    for c in missing:
        cid = c["chat_id"]
        title = c.get("title") or str(cid)
        url = f"https://t.me/{cid[1:]}" if isinstance(cid, str) and cid.startswith("@") \
              else f"https://t.me/c/{str(cid).replace('-100', '')}"
        buttons.append([InlineKeyboardButton(f"📢 {title}", url=url)])
    buttons.append([InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_join")])
    return InlineKeyboardMarkup(buttons)


def kb_cooldown(current_cd):
    opts = [("❌ بدون حد", 0), ("⏱️ ساعة", 1), ("⏱️ ساعتان", 2),
            ("⏱️ 6 ساعات", 6), ("⏱️ 12 ساعة", 12), ("⏱️ 24 ساعة", 24)]
    rows = []
    row = []
    for label, hrs in opts:
        prefix = "✅ " if (hrs == 0 and current_cd == 0) or (hrs > 0 and current_cd == hrs * 3600) else ""
        row.append(InlineKeyboardButton(f"{prefix}{label}", callback_data=f"admin_cd_set_{hrs}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row: rows.append(row)
    rows.append([InlineKeyboardButton("✏️ وقت مخصص", callback_data="admin_cd_custom"),
                 InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")])
    return InlineKeyboardMarkup(rows)


def kb_premium():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إضافة رقم بريميوم", callback_data="admin_prem_add")],
        [InlineKeyboardButton("➖ حذف رقم بريميوم", callback_data="admin_prem_del")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")],
    ])


def kb_force_join(enabled):
    rows = []
    if enabled:
        rows.append([InlineKeyboardButton("🔴 تعطيل الاشتراك الإجباري", callback_data="admin_fj_disable")])
    else:
        rows.append([InlineKeyboardButton("🟢 تفعيل الاشتراك الإجباري", callback_data="admin_fj_enable")])
    rows.append([InlineKeyboardButton("➕ إضافة قناة", callback_data="admin_fj_add_channel"),
                 InlineKeyboardButton("➖ حذف قناة", callback_data="admin_fj_del_channel")])
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")])
    return InlineKeyboardMarkup(rows)


def kb_reset():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ نعم، امسح كل شيء", callback_data="admin_reset_confirm")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="admin_panel")],
    ])


def kb_back_main():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="menu_back")]])


# ═══════════════════════════════════════════════════════════════
# CORE FLOW — تسجيل 2GB (per-user lock)
# ═══════════════════════════════════════════════════════════════

async def do_claim_2gb(context, chat_id, msisdn, user_data):
    """
    العملية الرئيسية — تعمل في task منفصل لكل مستخدم
    محمية بـ asyncio.Lock لكل chat_id لمنع الضغط المزدوج
    """
    lock = await get_user_lock(chat_id)
    async with lock:
        # قراءة user مع تأمين
        user = await db_get_user(chat_id)
        if not user:
            await safe_send(context, chat_id, "❌ جلسة منتهية — أعد /start")
            return

        # فحص cooldown
        last_claim = user.get("last_2gb_claim", {}).get(msisdn, 0)
        if last_claim:
            elapsed = int(time.time()) - int(last_claim)
            remaining = GIFT_2GB_COOLDOWN - elapsed
            if remaining > 0:
                await safe_send(context, chat_id, fmt_2gb_wait(remaining), reply_markup=kb_main(chat_id, len(user.get("msisdns", []))))
                return

        # رسالة بدء
        start_msg = await safe_send(context, chat_id, fmt_2gb_start())
        if not start_msg: return

        # استخراج بيانات الرقم
        num_data = user.get("numbers_data", {}).get(msisdn, {})
        num_data["msisdn"] = msisdn

        # استدعاء API
        res = await ooredoo_claim_2gb_gift(msisdn, num_data)

        # حفظ التحديثات (توكن محدّث مثلاً)
        if num_data.get("access_token") != user.get("numbers_data", {}).get(msisdn, {}).get("access_token"):
            user["numbers_data"][msisdn] = num_data
            await db_save_user(chat_id, user)

        if not res.get("success"):
            try:
                await context.bot.delete_message(chat_id, start_msg.message_id)
            except: pass
            if res.get("already_claimed"):
                await safe_send(context, chat_id, fmt_2gb_wait(GIFT_2GB_COOLDOWN),
                                reply_markup=kb_main(chat_id, len(user.get("msisdns", []))))
            else:
                await safe_send(context, chat_id, fmt_2gb_error(),
                                reply_markup=kb_main(chat_id, len(user.get("msisdns", []))))
            return

        # نجاح! تحديث DB
        user["last_2gb_claim"][msisdn] = int(time.time())
        user["last_activation_at"] = int(time.time())
        await db_save_user(chat_id, user)
        await db_inc_stat("total_activations", 1)
        await db_inc_stat("total_2gb_claims", 1)

        # رسالة النجاح
        await safe_edit(context, chat_id, start_msg.message_id, fmt_2gb_success(msisdn),
                        reply_markup=kb_main(chat_id, len(user.get("msisdns", []))))

        # إشعار القناة (غير حاجب)
        asyncio.create_task(_notify_channel(context, msisdn))


async def _notify_channel(context, msisdn):
    try:
        await context.bot.send_message(
            NOTIFY_CHANNEL_ID,
            f"<b>🎁 تفعيل 2GB</b>\n{LINE}\n📱 <b>الرقم:</b> <code>{mask_msisdn(msisdn)}</code>\n\n<i>⚡ by moon</i>",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logger.debug(f"notify failed: {e}")


# ═══════════════════════════════════════════════════════════════
# FORCE JOIN CHECK
# ═══════════════════════════════════════════════════════════════

async def check_force_join(context, user_id):
    if not await db_is_force_join_enabled():
        return True, []
    channels = await db_get_channels()
    if not channels:
        return True, []
    missing = []
    for c in channels:
        try:
            member = await context.bot.get_chat_member(c["chat_id"], user_id)
            if member.status in ("member", "administrator", "creator"):
                continue
            missing.append(c)
        except Exception:
            missing.append(c)
    return len(missing) == 0, missing


# ═══════════════════════════════════════════════════════════════
# HANDLERS — /start
# ═══════════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    joined, missing = await check_force_join(context, user_id)
    if not joined:
        await safe_send(context, chat_id, fmt_join_required(missing), reply_markup=kb_join(missing))
        return

    user = await db_get_user(chat_id)
    if user and user.get("msisdns"):
        await safe_send(context, chat_id, fmt_welcome_back_multi(user),
                        reply_markup=kb_main(chat_id, len(user["msisdns"])))
    else:
        clear_session(chat_id)
        set_session(chat_id, {"state": "awaiting_phone"})
        await safe_send(context, chat_id, fmt_welcome())


# ═══════════════════════════════════════════════════════════════
# HANDLERS — الرسائل النصية
# ═══════════════════════════════════════════════════════════════

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    # Force join check
    joined, missing = await check_force_join(context, user_id)
    if not joined and not is_admin(user_id):
        await safe_send(context, chat_id, fmt_join_required(missing), reply_markup=kb_join(missing))
        return

    # /admin
    if text.startswith("/admin") and is_admin(chat_id):
        await safe_send(context, chat_id, fmt_admin_panel(), reply_markup=kb_admin())
        return

    # /cancel broadcast
    if text == "/cancel" and chat_id in admin_states and admin_states[chat_id].get("action") == "broadcast":
        admin_states.pop(chat_id, None)
        await safe_send(context, chat_id, "✅ تم إلغاء الإذاعة", reply_markup=kb_admin())
        return

    # Admin states
    if chat_id in admin_states:
        await handle_admin_state(context, chat_id, text)
        return

    # Session flow
    sess = get_session(chat_id)
    state = sess.get("state", "")

    if state == "awaiting_phone":
        if not is_valid_ooredoo_number(text):
            await safe_send(context, chat_id, fmt_invalid_number())
            return
        digits = "".join(c for c in text if c.isdigit())
        msisdn = "213" + digits[1:]
        await process_phone(context, chat_id, user_id, msisdn)
        return

    if state == "awaiting_otp":
        if not text.isdigit() or len(text) != 6:
            await safe_send(context, chat_id, fmt_otp_invalid())
            return
        await process_otp(context, chat_id, user_id, text)
        return

    # Fallback
    await safe_send(context, chat_id, fmt_welcome())


async def process_phone(context, chat_id, user_id, msisdn):
    # فحص
    user = await db_get_user(chat_id)
    nums = user.get("msisdns", []) if user else []
    if len(nums) >= MAX_NUMBERS_PER_USER and msisdn not in nums:
        clear_session(chat_id)
        await safe_send(context, chat_id, fmt_limit_reached(),
                        reply_markup=kb_main(chat_id, len(nums)))
        return
    owner = await db_find_owner_of_msisdn(msisdn)
    if owner is not None and owner != chat_id:
        clear_session(chat_id)
        await safe_send(context, chat_id, fmt_number_taken(mask_msisdn(msisdn)))
        return

    # رقم محفوظ → تفعيل مباشر
    if msisdn in nums:
        clear_session(chat_id)
        asyncio.create_task(do_claim_2gb(context, chat_id, msisdn, None))
        return

    # OTP cooldown
    last_sent = otp_cooldown.get(msisdn, 0)
    if time.time() - last_sent < 40:
        await safe_send(context, chat_id, fmt_cooldown(int(40 - (time.time() - last_sent))))
        return

    # إرسال OTP
    set_session(chat_id, {"state": "sending_otp", "msisdn": msisdn})
    await safe_send(context, chat_id, fmt_otp_sending())

    device = get_device(chat_id)
    res = await ooredoo_send_otp(msisdn, device)
    if not res:
        await safe_send(context, chat_id, fmt_otp_failed())
        clear_session(chat_id)
        return
    otp_cooldown[msisdn] = time.time()
    set_session(chat_id, {
        "state": "awaiting_otp", "msisdn": msisdn,
        "proxy_host": res["proxy"]["host"] if res.get("proxy") else "",
        "proxy_user": res["proxy"]["userpass"] if res.get("proxy") else "",
    })
    await safe_send(context, chat_id, fmt_otp_sent())


async def process_otp(context, chat_id, user_id, otp):
    sess = get_session(chat_id)
    msisdn = sess.get("msisdn")
    proxy = {"host": sess.get("proxy_host", ""), "userpass": sess.get("proxy_user", "")}

    vm = await safe_send(context, chat_id, fmt_otp_verifying())
    res = await ooredoo_verify_otp(msisdn, otp, proxy, get_device(chat_id))

    if vm:
        try: await context.bot.delete_message(chat_id, vm.message_id)
        except: pass

    if res == "wrong_otp":
        await safe_send(context, chat_id, fmt_otp_wrong())
        return
    if not res:
        await safe_send(context, chat_id, fmt_2gb_error())
        clear_session(chat_id)
        return

    # فحص أخير
    user = await db_get_user(chat_id)
    if user and len(user.get("msisdns", [])) >= MAX_NUMBERS_PER_USER:
        clear_session(chat_id)
        await safe_send(context, chat_id, fmt_limit_reached(),
                        reply_markup=kb_main(chat_id, len(user.get("msisdns", []))))
        return
    owner = await db_find_owner_of_msisdn(msisdn)
    if owner is not None and owner != chat_id:
        clear_session(chat_id)
        await safe_send(context, chat_id, fmt_number_taken(mask_msisdn(msisdn)))
        return

    # حفظ
    if not user:
        user = {"created_at": int(time.time()), "msisdns": [], "numbers_data": {},
                "last_2gb_claim": {}, "last_activation_at": 0}
    user["numbers_data"][msisdn] = res
    if msisdn not in user["msisdns"]:
        user["msisdns"].append(msisdn)
    user["msisdn"] = msisdn
    await db_save_user(chat_id, user)
    await db_inc_stat("total_users", 1)
    clear_session(chat_id)

    await safe_send(context, chat_id, fmt_login_success(mask_msisdn(msisdn)),
                    reply_markup=kb_main(chat_id, len(user["msisdns"])))


# ═══════════════════════════════════════════════════════════════
# ADMIN STATE HANDLER
# ═══════════════════════════════════════════════════════════════

async def handle_admin_state(context, chat_id, text):
    state = admin_states[chat_id]
    action = state.get("action")

    if action == "broadcast":
        admin_states.pop(chat_id, None)
        await do_broadcast(context, chat_id, text)
        return

    if action == "prem_add":
        msisdn = normalize_msisdn(text)
        if not msisdn:
            await safe_send(context, chat_id, "❌ رقم غير صالح")
            return
        if await db_is_premium(msisdn):
            await safe_send(context, chat_id, f"⚠️ الرقم بريميوم مسبقاً")
            return
        await db_add_premium(msisdn, chat_id)
        admin_states.pop(chat_id, None)
        await safe_send(context, chat_id, f"✅ تمت إضافة <code>{mask_msisdn(msisdn)}</code>", reply_markup=kb_admin())
        return

    if action == "prem_del":
        msisdn = normalize_msisdn(text)
        if not msisdn:
            await safe_send(context, chat_id, "❌ رقم غير صالح")
            return
        if await db_remove_premium(msisdn):
            admin_states.pop(chat_id, None)
            await safe_send(context, chat_id, f"✅ تم الحذف", reply_markup=kb_admin())
        else:
            await safe_send(context, chat_id, "⚠️ غير موجود")
        return

    if action == "cd_custom":
        try:
            hours = float(text)
            if hours < 0 or hours > 8760: raise ValueError
        except:
            await safe_send(context, chat_id, "❌ أرسل عدد ساعات (0-8760)")
            return
        await db_set_setting("cooldown_mode", "custom" if hours > 0 else "unlimited")
        await db_set_setting("cooldown_hours", str(hours))
        admin_states.pop(chat_id, None)
        cd_str = "بدون حد ♾️" if hours == 0 else format_duration(int(hours * 3600))
        await safe_send(context, chat_id, f"✅ تم التحديث: <code>{cd_str}</code>", reply_markup=kb_admin())
        return

    if action == "fj_add_channel":
        raw = text.strip()
        cid = raw
        m = re.match(r'https?://t\.me/([A-Za-z0-9_]+)', raw)
        if m: cid = "@" + m.group(1)
        title = ""
        try:
            info = await context.bot.get_chat(cid)
            title = info.title or info.username or cid
        except Exception:
            await safe_send(context, chat_id, "❌ لم أستطع الوصول — تأكد أن البوت أدمن")
            return
        ok = await db_add_channel(cid, title)
        admin_states.pop(chat_id, None)
        if ok:
            await safe_send(context, chat_id, f"✅ تمت الإضافة: {title}", reply_markup=kb_force_join(await db_is_force_join_enabled()))
        else:
            await safe_send(context, chat_id, "⚠️ موجودة مسبقاً", reply_markup=kb_force_join(await db_is_force_join_enabled()))
        return

    if action == "fj_del_channel":
        raw = text.strip()
        m = re.match(r'https?://t\.me/([A-Za-z0-9_]+)', raw)
        if m: raw = "@" + m.group(1)
        if await db_remove_channel(raw):
            admin_states.pop(chat_id, None)
            await safe_send(context, chat_id, f"✅ تم الحذف", reply_markup=kb_force_join(await db_is_force_join_enabled()))
        else:
            await safe_send(context, chat_id, "⚠️ غير موجودة")
        return


async def do_broadcast(context, chat_id, msg):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT chat_id FROM users") as cur:
            ids = [row[0] async for row in cur]
    total = len(ids)
    if total == 0:
        await safe_send(context, chat_id, "⚠️ لا يوجد مستخدمون", reply_markup=kb_admin())
        return

    status_msg = await safe_send(context, chat_id, f"📢 جاري الإرسال... (0/{total})")

    success = 0; failed = 0
    for i, cid in enumerate(ids, 1):
        try:
            await context.bot.send_message(cid, msg, parse_mode=ParseMode.HTML)
            success += 1
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await context.bot.send_message(cid, msg, parse_mode=ParseMode.HTML)
                success += 1
            except: failed += 1
        except: failed += 1

        if i % 20 == 0 and status_msg:
            await safe_edit(context, chat_id, status_msg.message_id,
                            f"📢 جاري الإرسال... ({i}/{total})\n✅ {success} | ❌ {failed}")
        await asyncio.sleep(0.04)

    if status_msg:
        await safe_edit(context, chat_id, status_msg.message_id,
                        f"✅ تمت الإذاعة\n\n📊 المجموع: {total}\n✅ نجح: {success}\n❌ فشل: {failed}",
                        reply_markup=kb_admin())


# ═══════════════════════════════════════════════════════════════
# CALLBACK HANDLER
# ═══════════════════════════════════════════════════════════════

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat.id
    data = query.data
    user_id = query.from_user.id

    try:
        await query.answer()
    except: pass

    try:
        if data == "check_join":
            joined, missing = await check_force_join(context, user_id)
            if joined:
                user = await db_get_user(chat_id)
                if user and user.get("msisdns"):
                    txt = fmt_welcome_back_multi(user)
                    await safe_edit(context, chat_id, query.message.message_id, txt,
                                    reply_markup=kb_main(chat_id, len(user["msisdns"])))
                else:
                    set_session(chat_id, {"state": "awaiting_phone"})
                    await safe_edit(context, chat_id, query.message.message_id, fmt_welcome())
            else:
                await safe_edit(context, chat_id, query.message.message_id,
                                fmt_join_required(missing), reply_markup=kb_join(missing))
            return

        if data == "menu_claim_2gb":
            user = await db_get_user(chat_id)
            if not user or not user.get("msisdns"):
                await query.answer("❌ لا يوجد رقم مسجل", show_alert=True)
                return
            nums = user["msisdns"]
            if len(nums) == 1:
                # إطلاق task منفصل
                asyncio.create_task(do_claim_2gb(context, chat_id, nums[0], None))
                return
            # أكثر من رقم
            rows = []
            for m in nums:
                last = user.get("last_2gb_claim", {}).get(m, 0)
                elapsed = int(time.time()) - int(last) if last else GIFT_2GB_COOLDOWN
                remaining = max(0, GIFT_2GB_COOLDOWN - elapsed)
                label = f"🎁 {mask_msisdn(m)} ✅" if remaining == 0 else f"⏳ {mask_msisdn(m)} ({format_duration(remaining)})"
                rows.append([InlineKeyboardButton(label, callback_data=f"claim_for_{m}")])
            rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="menu_back")])
            await safe_edit(context, chat_id, query.message.message_id,
                            "🎁 <b>اختر الرقم</b>\n\n" + LINE_LIGHT + "\n\n👇",
                            reply_markup=InlineKeyboardMarkup(rows))
            return

        if data.startswith("claim_for_"):
            msisdn = data.replace("claim_for_", "")
            user = await db_get_user(chat_id)
            if not user or msisdn not in user.get("msisdns", []):
                await query.answer("❌ رقم غير مسجل", show_alert=True)
                return
            last = user.get("last_2gb_claim", {}).get(msisdn, 0)
            if last:
                remaining = GIFT_2GB_COOLDOWN - (int(time.time()) - int(last))
                if remaining > 0:
                    await query.answer("⏳ انتظر 24 ساعة", show_alert=True)
                    return
            asyncio.create_task(do_claim_2gb(context, chat_id, msisdn, None))
            return

        if data == "menu_back":
            user = await db_get_user(chat_id)
            if user and user.get("msisdns"):
                await safe_edit(context, chat_id, query.message.message_id,
                                fmt_welcome_back_multi(user),
                                reply_markup=kb_main(chat_id, len(user["msisdns"])))
            else:
                await safe_edit(context, chat_id, query.message.message_id, fmt_welcome())
            return

        if data == "menu_add_number":
            user = await db_get_user(chat_id)
            count = len(user.get("msisdns", [])) if user else 0
            if count >= MAX_NUMBERS_PER_USER:
                await query.answer("❌ وصلت للحد الأقصى", show_alert=True)
                return
            clear_session(chat_id)
            set_session(chat_id, {"state": "awaiting_phone", "adding_number": True})
            await safe_edit(context, chat_id, query.message.message_id, fmt_add_number())
            return

        if data == "menu_relogin":
            await db_delete_user(chat_id)
            clear_session(chat_id)
            set_session(chat_id, {"state": "awaiting_phone"})
            await safe_edit(context, chat_id, query.message.message_id, fmt_relogin())
            return

        # ADMIN CALLBACKS
        if data.startswith("admin_"):
            if not is_admin(chat_id):
                await query.answer("❌ ليس لديك صلاحية", show_alert=True)
                return
            await handle_admin_callback(context, query, chat_id, data)
            return

    except Exception as e:
        logger.exception(f"Callback error: {e}")


async def handle_admin_callback(context, query, chat_id, data):
    if data == "admin_back_main":
        user = await db_get_user(chat_id)
        if user and user.get("msisdns"):
            await safe_edit(context, chat_id, query.message.message_id,
                            fmt_welcome_back_multi(user),
                            reply_markup=kb_main(chat_id, len(user["msisdns"])))
        else:
            await safe_edit(context, chat_id, query.message.message_id, fmt_welcome())
        return

    if data == "admin_panel":
        await safe_edit(context, chat_id, query.message.message_id, fmt_admin_panel(), reply_markup=kb_admin())
        return

    if data == "admin_stats":
        total_users = await db_count_users()
        total_premium = await db_count_premium()
        total_activations = await db_get_stat("total_activations")
        total_2gb = await db_get_stat("total_2gb_claims")
        started = await db_get_stat("started_at", int(time.time()))
        uptime = int(time.time()) - started
        fj = "✅ مفعل" if await db_is_force_join_enabled() else "❌ معطل"
        chs = await db_get_channels()
        txt = (
            f"╭━━━━━━━━━━━━━━━━━━━━━━╮\n"
            f"   <b>📊 الإحصائيات</b>\n"
            f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            f"👥 <b>المستخدمون:</b> <code>{total_users}</code>\n"
            f"⭐ <b>البريميوم:</b> <code>{total_premium}</code>\n"
            f"⚡ <b>إجمالي التفعيلات:</b> <code>{total_activations}</code>\n"
            f"🎁 <b>هدايا 2GB:</b> <code>{total_2gb}</code>\n"
            f"🔐 <b>الاشتراك:</b> <code>{fj}</code>\n"
            f"📢 <b>القنوات:</b> <code>{len(chs)}</code>\n"
            f"🕐 <b>مدة التشغيل:</b> <code>{format_duration(uptime)}</code>"
        )
        await safe_edit(context, chat_id, query.message.message_id, txt, reply_markup=kb_admin())
        return

    if data == "admin_cooldown":
        cd = await db_get_cooldown_seconds()
        cd_str = "بدون حد ♾️" if cd == 0 else format_duration(cd)
        txt = (
            f"╭━━━━━━━━━━━━━━━━━━━━━━╮\n"
            f"   <b>⏱️ وقت الانتظار</b>\n"
            f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            f"<b>الحالي:</b> <code>{cd_str}</code>\n\n"
            f"{LINE}\n\nاختر إعداداً جديداً 👇"
        )
        await safe_edit(context, chat_id, query.message.message_id, txt, reply_markup=kb_cooldown(cd))
        return

    if data.startswith("admin_cd_set_"):
        hours = int(data.split("_")[-1])
        await db_set_setting("cooldown_mode", "custom" if hours > 0 else "unlimited")
        await db_set_setting("cooldown_hours", str(hours))
        await query.answer(f"✅ {hours or 'بدون'} ساعة")
        cd = await db_get_cooldown_seconds()
        txt = f"⏱️ الحالي: <code>{'بدون حد ♾️' if cd == 0 else format_duration(cd)}</code>"
        await safe_edit(context, chat_id, query.message.message_id, txt, reply_markup=kb_cooldown(cd))
        return

    if data == "admin_cd_custom":
        admin_states[chat_id] = {"action": "cd_custom"}
        await safe_send(context, chat_id, "✏️ أرسل عدد الساعات (0 = بدون حد)")
        return

    if data == "admin_premium":
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT msisdn FROM premium LIMIT 20") as cur:
                rows = [r[0] async for r in cur]
        count = await db_count_premium()
        lines = [f"⭐ <b>البريميوم</b> ({count})", "", LINE]
        for i, m in enumerate(rows, 1):
            lines.append(f"  {i}. <code>{mask_msisdn(m)}</code>")
        if count == 0:
            lines.append("<i>لا يوجد</i>")
        await safe_edit(context, chat_id, query.message.message_id, "\n".join(lines), reply_markup=kb_premium())
        return

    if data == "admin_prem_add":
        admin_states[chat_id] = {"action": "prem_add"}
        await safe_send(context, chat_id, "➕ أرسل الرقم")
        return

    if data == "admin_prem_del":
        admin_states[chat_id] = {"action": "prem_del"}
        await safe_send(context, chat_id, "➖ أرسل الرقم")
        return

    if data == "admin_force_join":
        enabled = await db_is_force_join_enabled()
        chs = await db_get_channels()
        lines = [f"🔐 <b>الاشتراك الإجباري</b>", "",
                 f"الحالة: {'✅ مفعل' if enabled else '❌ معطل'}",
                 f"القنوات: {len(chs)}", "", LINE]
        for c in chs:
            lines.append(f"  • {c['title']}  <code>{c['chat_id']}</code>")
        await safe_edit(context, chat_id, query.message.message_id, "\n".join(lines), reply_markup=kb_force_join(enabled))
        return

    if data == "admin_fj_enable":
        await db_set_setting("force_join_enabled", "true")
        await query.answer("✅ مفعل")
        await handle_admin_callback(context, query, chat_id, "admin_force_join")
        return

    if data == "admin_fj_disable":
        await db_set_setting("force_join_enabled", "false")
        await query.answer("✅ معطل")
        await handle_admin_callback(context, query, chat_id, "admin_force_join")
        return

    if data == "admin_fj_add_channel":
        admin_states[chat_id] = {"action": "fj_add_channel"}
        await safe_send(context, chat_id, "➕ أرسل @username أو -100xxx أو رابط")
        return

    if data == "admin_fj_del_channel":
        admin_states[chat_id] = {"action": "fj_del_channel"}
        await safe_send(context, chat_id, "➖ أرسل معرف القناة")
        return

    if data == "admin_broadcast":
        admin_states[chat_id] = {"action": "broadcast"}
        await safe_edit(context, chat_id, query.message.message_id, "📢 أرسل الرسالة الآن (/cancel للإلغاء)")
        return

    if data == "admin_reset":
        txt = ("🗑️ <b>محو البيانات</b>\n\n⚠️ تحذير — لا يمكن التراجع!")
        await safe_edit(context, chat_id, query.message.message_id, txt, reply_markup=kb_reset())
        return

    if data == "admin_reset_confirm":
        async with aiosqlite.connect(DB_PATH) as db:
            for tbl in ("users", "premium", "channels"):
                await db.execute(f"DELETE FROM {tbl}")
            await db.execute("UPDATE stats SET value = 0 WHERE key != 'started_at'")
            await db.execute("UPDATE stats SET value = ? WHERE key = 'started_at'", (int(time.time()),))
            await db.commit()
        await query.answer("✅ تم المحو", show_alert=True)
        await safe_edit(context, chat_id, query.message.message_id, "✅ تم مسح كل البيانات", reply_markup=kb_admin())
        return


def fmt_admin_panel():
    return (
        f"╭━━━━━━━━━━━━━━━━━━━━━━╮\n"
        f"   <b>👑 لوحة الأدمن</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"اختر القسم 👇"
    )


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

async def post_init(app: Application):
    await init_db()
    logger.info("=" * 60)
    logger.info("🚀 by moon v3.0.0 — ASYNC EDITION")
    logger.info(f"⚡ Max concurrent Ooredoo: {MAX_CONCURRENT_OOREDOO}")
    logger.info(f"⚡ Max concurrent Telegram: {MAX_CONCURRENT_TG}")
    logger.info(f"🗄️ DB: {DB_PATH} (WAL mode)")
    logger.info("=" * 60)


async def post_shutdown(app: Application):
    await close_http_client()
    logger.info("🛑 Shutdown complete")


def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)   # ⚡ معالجة متزامنة للتحديثات
        .connection_pool_size(256)  # ⚡ pool أكبر
        .pool_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .connect_timeout(15.0)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("admin", lambda u, c: cmd_start(u, c)))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("🚀 Starting bot...")
    app.run_polling(
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
