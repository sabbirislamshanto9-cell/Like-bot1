#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          AS LIKE BOT - Telegram Bot                         ║
║           Free Fire Auto Like Bot                                ║
║           AS LIKE BOT                                        ║
╚══════════════════════════════════════════════════════════════════╝

Setup:
1. pip install python-telegram-bot aiohttp
2. Fill in BOT_TOKEN and ADMIN_ID below
3. Add your channel links in REQUIRED_CHANNELS
4. python main.py
"""

import os
import json
import random
import asyncio
import logging
import aiohttp
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from aiohttp import web

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION - EDIT THESE VALUES
# ═══════════════════════════════════════════════════════════════════

BOT_TOKEN = "8832692794:AAGMCR2XmbnhGfxxLxgUggNt9y9a3GRqjKI"  # Paste your Telegram bot token here
ADMIN_ID = 7510853558                        # Your Telegram numeric ID

# Single API Config
API_BASE = "https://aryan-shanto-fflikebot2-0.vercel.app/like"
# API_KEY IS NO LONGER USED AS PER YOUR REQUEST

# Pre-Authorized Groups/Channels list (These don't need manual /allow command)
PRE_AUTHORIZED_GROUPS = [
    -1004220352794,                          # Replace with your actual Channel/Group Chat ID
]

# Required channels users MUST join
REQUIRED_CHANNELS = [
    {"name": "Channel 1", "link": "https://t.me/SadSong_official"},
]

# Daily reset time (4:00 AM)
RESET_HOUR = 4
RESET_MINUTE = 0
BD_TZ = ZoneInfo("Asia/Dhaka")
AUTO_LIKE_DAILY_ESTIMATE = 100  # Editable from admin command

# Auto-like time (5:00 AM)
AUTO_LIKE_HOUR = 5
AUTO_LIKE_MINUTE = 0

# Valid Free Fire regions
FIXED_REGION = "BD"

# AS LIKE BOT - USER MENU / BALANCE / REFERRAL CONFIG
BOT_NAME = "AS LIKE BOT"
ADMIN_USERNAME = "As_owner99"
ADMIN_URL = "https://t.me/As_owner99"
REFERRAL_REWARD = 5
REFERRAL_MIN_NEW_USER = True
# These packages are shown in the menu but are not orderable yet.
COMING_SOON_PACKAGES = {5000, 10000}

# Change these prices whenever you want.
AUTO_LIKE_PACKAGES = [
    (100, 5),
    (200, 10),
    (500, 25),
    (1000, 40),
    (2000, 60),
    (5000, 100),
    (10000, 200),
]


# ═══════════════════════════════════════════════════════════════════
# EMOJI POOL - Random emojis for each user
# ═══════════════════════════════════════════════════════════════════

EMOJI_POOL = [
    "🔥", "⚡", "🎯", "🏆", "💎", "🚀", "⭐", "💥",
    "🎮", "🎲", "🎪", "🎭", "🎨", "🎰", "🎱", "🎳",
    "🎸", "🎺", "🎻", "🎹", "🎷", "🎤", "🎧", "🎬",
    "🌟", "✨", "💫", "🌠", "🌈", "☄️", "🔮", "💀",
    "👑", "🎓", "🎖️", "🏅", "🥇", "🥈", "🥉", "🎁",
    "🎀", "🎊", "🎉", "🎈", "🎄", "🎃", "🎅", "🤖",
    "👾", "👽", "🛸", "🌍", "🌎", "🌏", "🌕", "☀️",
]

# ═══════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# DATA MANAGER - JSON File Storage
# ═══════════════════════════════════════════════════════════════════

DATA_DIR = "bot_data"
os.makedirs(DATA_DIR, exist_ok=True)

FILES = {
    "users": os.path.join(DATA_DIR, "users.json"),
    "groups": os.path.join(DATA_DIR, "groups.json"),
    "channels": os.path.join(DATA_DIR, "channels.json"),
    "auto_like": os.path.join(DATA_DIR, "auto_like.json"),
    "target_like": os.path.join(DATA_DIR, "target_like.json"),
    "daily_usage": os.path.join(DATA_DIR, "daily_usage.json"),
    "unlimited": os.path.join(DATA_DIR, "unlimited.json"),
    "vip": os.path.join(DATA_DIR, "vip.json"),
    "broadcast_users": os.path.join(DATA_DIR, "broadcast_users.json"),
    "group_status": os.path.join(DATA_DIR, "group_status.json"),
    "like_stats": os.path.join(DATA_DIR, "like_stats.json"),
    "user_stats": os.path.join(DATA_DIR, "user_stats.json"),
    "referrals": os.path.join(DATA_DIR, "referrals.json"),
    "orders": os.path.join(DATA_DIR, "orders.json"),
    "packages": os.path.join(DATA_DIR, "packages.json"),
}


def load_data(key):
    path = FILES.get(key)
    if not path:
        return {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            logger.exception("Failed to load data file: %s", path)
            return {}
    return {}


def save_data(key, data):
    path = FILES.get(key)
    if not path:
        return False
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
        return True
    except Exception:
        logger.exception("Failed to save data file: %s", path)
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass
        return False


def load_packages():
    """Load editable package configuration from JSON, falling back to defaults."""
    default_packages = [(int(likes), int(price)) for likes, price in AUTO_LIKE_PACKAGES]
    try:
        data = load_data("packages")
        if isinstance(data, list) and data:
            packages = []
            for item in data:
                if isinstance(item, dict):
                    likes = int(item.get("likes", 0))
                    price = int(item.get("price", 0))
                elif isinstance(item, (list, tuple)) and len(item) == 2:
                    likes, price = int(item[0]), int(item[1])
                else:
                    continue
                if likes > 0 and price >= 0:
                    packages.append((likes, price))
            if packages:
                return sorted(set(packages), key=lambda x: x[0])
    except Exception as e:
        logger.error("Failed to load packages.json: %s", e)
    return sorted(default_packages, key=lambda x: x[0])


def save_packages(packages):
    """Persist packages so admin edits survive bot restarts."""
    clean = []
    seen = set()
    for likes, price in packages:
        likes, price = int(likes), int(price)
        if likes > 0 and price >= 0 and likes not in seen:
            clean.append((likes, price))
            seen.add(likes)
    clean.sort(key=lambda x: x[0])
    save_data("packages", [{"likes": likes, "price": price} for likes, price in clean])
    return clean


# Load the editable package list once the data manager is ready.
AUTO_LIKE_PACKAGES = load_packages()


# ═══════════════════════════════════════════════════════════════════
# FORMATTING HELPERS
# ═══════════════════════════════════════════════════════════════════

def format_bold(text):
    """Format text so that every non-empty line is styled in bold (*bold*) with absolutely NO blockquotes (>)"""
    lines = text.split("\n")
    formatted_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            clean = stripped.replace("*", "").replace(">", "").strip()
            clean = clean.replace("_", r"\_")
            if clean:
                formatted_lines.append(f"*{clean}*")
            else:
                formatted_lines.append("")
        else:
            formatted_lines.append("")
    return "\n".join(formatted_lines)


def is_admin(user_id):
    return user_id == ADMIN_ID


def now_bd():
    return datetime.now(BD_TZ)

def get_today():
    return now_bd().strftime("%Y-%m-%d")

def bd_timestamp():
    return now_bd().strftime("%Y-%m-%d %H:%M:%S")


def can_use_like(user_id):
    """Check if user can use /like today - ADMIN ALWAYS BYPASSED"""
    if is_admin(user_id) or is_vip(user_id):
        return True
    usage = load_data("daily_usage")
    uid = str(user_id)
    today = get_today()
    if uid not in usage:
        return True
    return usage[uid].get("date") != today


def mark_like_used(user_id):
    """Mark that user has used /like today - SKIP ADMIN"""
    if is_admin(user_id) or is_vip(user_id):
        return
    usage = load_data("daily_usage")
    uid = str(user_id)
    usage[uid] = {"date": get_today(), "count": 1}
    save_data("daily_usage", usage)


def reset_daily_usage():
    """Reset daily usage at 4 AM"""
    save_data("daily_usage", {})
    logger.info("Daily usage reset at 4:00 AM")


def is_group_allowed(chat_id):
    """Check if group is allowed (Pre-authorized lists always return True)"""
    if chat_id in PRE_AUTHORIZED_GROUPS:
        return True
    groups = load_data("groups")
    return str(chat_id) in groups


def is_group_enabled(chat_id):
    """Return True when group commands are enabled. Default is ON."""
    statuses = load_data("group_status")
    return statuses.get(str(chat_id), {}).get("enabled", True)


def set_group_enabled(chat_id, enabled):
    statuses = load_data("group_status")
    statuses[str(chat_id)] = {
        "enabled": bool(enabled),
        "updated_at": datetime.now().isoformat()
    }
    save_data("group_status", statuses)


def allow_group(chat_id):
    """Allow bot to work in a group"""
    groups = load_data("groups")
    groups[str(chat_id)] = {"allowed": True, "added_at": datetime.now().isoformat()}
    save_data("groups", groups)


def remove_group(chat_id):
    """Remove group from allowed list"""
    groups = load_data("groups")
    if str(chat_id) in groups:
        del groups[str(chat_id)]
        save_data("groups", groups)


def add_channel(name, link):
    """Add verification channel"""
    channels = load_data("channels")
    channels[name] = {"link": link, "added_at": datetime.now().isoformat()}
    save_data("channels", channels)


def remove_channel(name):
    """Remove verification channel"""
    channels = load_data("channels")
    if name in channels:
        del channels[name]
        save_data("channels", channels)


def get_channels():
    """Get verification channels, excluding the removed AS LIKE BOT channel."""
    channels = load_data("channels")
    if "Channel 2" in channels:
        channels.pop("Channel 2", None)
        save_data("channels", channels)
    return channels


def add_auto_like(uid, region, days):
    """Add UID to auto-like list with duration in days"""
    auto = load_data("auto_like")
    auto[str(uid)] = {
        "region": region.upper(),
        "days_left": int(days),
        "added_at": datetime.now().isoformat()
    }
    save_data("auto_like", auto)


def remove_auto_like(uid):
    """Remove UID from auto-like list"""
    auto = load_data("auto_like")
    if str(uid) in auto:
        del auto[str(uid)]
        save_data("auto_like", auto)


def get_auto_like_list():
    """Get all auto-like UIDs"""
    return load_data("auto_like")


def record_like_stats(uid, likes_given, source="manual"):
    """Record total and today's likes for a UID."""
    stats = load_data("like_stats")
    key = str(uid)
    today = get_today()

    info = stats.get(key, {
        "total_likes": 0,
        "today_likes": 0,
        "date": today,
        "runs": 0,
        "last_likes": 0,
    })

    if info.get("date") != today:
        info["date"] = today
        info["today_likes"] = 0

    try:
        likes_given = int(likes_given or 0)
    except (ValueError, TypeError):
        likes_given = 0

    info["total_likes"] = int(info.get("total_likes", 0)) + max(0, likes_given)
    info["today_likes"] = int(info.get("today_likes", 0)) + max(0, likes_given)
    info["runs"] = int(info.get("runs", 0)) + 1
    info["last_likes"] = max(0, likes_given)
    info["last_at"] = datetime.now().isoformat()

    stats[key] = info
    save_data("like_stats", stats)


def get_like_stats(uid):
    """Return stored like statistics for a UID."""
    stats = load_data("like_stats")
    key = str(uid)
    info = stats.get(key, {})
    today = get_today()

    if info.get("date") != today:
        info["today_likes"] = 0

    return {
        "total_likes": int(info.get("total_likes", 0)),
        "today_likes": int(info.get("today_likes", 0)),
        "runs": int(info.get("runs", 0)),
        "last_likes": int(info.get("last_likes", 0)),
        "last_at": info.get("last_at", "N/A"),
    }


def add_target_like(uid, region, target_limit):
    """Add UID with target likes limit"""
    targets = load_data("target_like")
    targets[str(uid)] = {
        "region": region.upper(),
        "target_limit": int(target_limit),
        "likes_sent": 0,
        "added_at": datetime.now().isoformat()
    }
    save_data("target_like", targets)


def remove_target_like(uid):
    """Remove UID from target like list"""
    targets = load_data("target_like")
    if str(uid) in targets:
        del targets[str(uid)]
        save_data("target_like", targets)


def add_unlimited(uid, region):
    """Add UID to unlimited likes list"""
    unlimited = load_data("unlimited")
    unlimited[uid] = {"region": region.upper(), "added_at": datetime.now().isoformat()}
    save_data("unlimited", unlimited)


def remove_unlimited(uid):
    """Remove UID from unlimited list"""
    unlimited = load_data("unlimited")
    if uid in unlimited:
        del unlimited[uid]
        save_data("unlimited", unlimited)


def is_unlimited(uid):
    """Check if UID has unlimited likes"""
    unlimited = load_data("unlimited")
    return uid in unlimited


def add_vip(user_id, days):
    """Add a Telegram user to VIP for a number of days."""
    vip = load_data("vip")
    start = datetime.now()
    vip[str(user_id)] = {
        "days": int(days),
        "expires_at": (start + timedelta(days=int(days))).isoformat(),
        "added_at": start.isoformat(),
    }
    save_data("vip", vip)


def remove_vip(user_id):
    """Remove a Telegram user from VIP."""
    vip = load_data("vip")
    vip.pop(str(user_id), None)
    save_data("vip", vip)


def is_vip(user_id):
    """Return True while the user's VIP period is active."""
    vip = load_data("vip")
    info = vip.get(str(user_id))
    if not info:
        return False
    try:
        expires_at = datetime.fromisoformat(info["expires_at"])
    except (KeyError, ValueError, TypeError):
        remove_vip(user_id)
        return False
    if datetime.now() >= expires_at:
        remove_vip(user_id)
        return False
    return True


def add_broadcast_user(user_id):
    """Add user to broadcast list"""
    users = load_data("broadcast_users")
    users[str(user_id)] = True
    save_data("broadcast_users", users)


def get_broadcast_users():
    """Get all broadcast user IDs"""
    users = load_data("broadcast_users")
    return [int(uid) for uid in users.keys()]


def get_user_emoji(user_id):
    """Get a consistent random emoji for each user"""
    users = load_data("users")
    uid = str(user_id)
    if uid not in users:
        users[uid] = {"emoji": random.choice(EMOJI_POOL), "balance": 0}
        save_data("users", users)
    return users[uid].get("emoji", "🔥")


# ═══════════════════════════════════════════════════════════════════
# USER BALANCE / REFERRAL / HISTORY
# ═══════════════════════════════════════════════════════════════════

def ensure_user(user_id, telegram_user=None):
    users = load_data("users")
    uid = str(user_id)
    if uid not in users:
        users[uid] = {"emoji": random.choice(EMOJI_POOL), "balance": 0, "referrals": 0}
    users[uid].setdefault("balance", 0)
    users[uid].setdefault("referrals", 0)
    if telegram_user is not None:
        users[uid]["first_name"] = telegram_user.first_name or "Unknown"
        users[uid]["username"] = telegram_user.username or ""
    save_data("users", users)
    return users[uid]


def get_balance(user_id):
    return int(ensure_user(user_id).get("balance", 0))


def add_balance(user_id, amount):
    users = load_data("users")
    uid = str(user_id)
    users.setdefault(uid, {"emoji": random.choice(EMOJI_POOL)})
    users[uid]["balance"] = int(users[uid].get("balance", 0)) + int(amount)
    save_data("users", users)
    return users[uid]["balance"]


def set_balance(user_id, amount):
    users = load_data("users")
    uid = str(user_id)
    users.setdefault(uid, {"emoji": random.choice(EMOJI_POOL)})
    users[uid]["balance"] = max(0, int(amount))
    save_data("users", users)
    return users[uid]["balance"]


def record_user_like_usage(user_id, likes_given):
    stats = load_data("user_stats")
    key = str(user_id)
    today = get_today()
    info = stats.get(key, {"total_likes": 0, "today_likes": 0, "date": today, "runs": 0})
    if info.get("date") != today:
        info["date"] = today
        info["today_likes"] = 0
    try:
        likes_given = max(0, int(likes_given or 0))
    except (ValueError, TypeError):
        likes_given = 0
    info["total_likes"] = int(info.get("total_likes", 0)) + likes_given
    info["today_likes"] = int(info.get("today_likes", 0)) + likes_given
    info["runs"] = int(info.get("runs", 0)) + 1
    info["last_likes"] = likes_given
    info["last_at"] = datetime.now().isoformat()
    stats[key] = info
    save_data("user_stats", stats)


def get_user_like_usage(user_id):
    stats = load_data("user_stats")
    info = stats.get(str(user_id), {})
    if info.get("date") != get_today():
        info["today_likes"] = 0
    return {
        "total_likes": int(info.get("total_likes", 0)),
        "today_likes": int(info.get("today_likes", 0)),
        "runs": int(info.get("runs", 0)),
        "last_likes": int(info.get("last_likes", 0)),
    }


def process_referral(user_id, payload):
    """Register one genuine /start referral and persist the reward exactly once."""
    if not payload or not str(payload).startswith("ref_"):
        return None

    referrer = str(payload)[4:].strip()
    uid = str(user_id)
    if not referrer.isdigit() or referrer == uid:
        return None

    referrals = load_data("referrals")
    if not isinstance(referrals, dict):
        referrals = {}
    if uid in referrals:
        return None

    users = load_data("users")
    if not isinstance(users, dict):
        users = {}
    users.setdefault(referrer, {"emoji": random.choice(EMOJI_POOL), "balance": 0, "referrals": 0})
    users[referrer].setdefault("balance", 0)
    users[referrer].setdefault("referrals", 0)

    reward = int(REFERRAL_REWARD)
    referrals[uid] = {
        "referrer": referrer,
        "reward": reward,
        "created_at": datetime.now().isoformat(),
    }
    users[referrer]["referrals"] = int(users[referrer].get("referrals", 0)) + 1
    users[referrer]["balance"] = int(users[referrer].get("balance", 0)) + reward

    # Persist both records. If either write fails, surface the error rather than
    # silently telling the user the referral succeeded.
    save_data("referrals", referrals)
    save_data("users", users)
    new_balance = int(users[referrer]["balance"])
    logger.info("Referral success: new_user=%s referrer=%s reward=%s balance=%s",
                uid, referrer, reward, new_balance)
    return {"referrer": int(referrer), "reward": reward, "balance": new_balance}


def get_referral_stats(user_id):
    referrals = load_data("referrals")
    mine = [info for info in referrals.values() if str(info.get("referrer")) == str(user_id)]
    return {"count": len(mine), "earned": sum(int(x.get("reward", 0)) for x in mine)}



def _next_order_id():
    orders = load_data("orders")
    if not isinstance(orders, dict):
        orders = {}
    nums = []
    for key in orders:
        try:
            nums.append(int(str(key).replace("AS", "")))
        except Exception:
            pass
    return f"AS{(max(nums) + 1 if nums else 1001)}"


def create_order(user_id, uid, likes_requested, price):
    orders = load_data("orders")
    if not isinstance(orders, dict):
        orders = {}
    order_id = _next_order_id()
    orders[order_id] = {
        "order_id": order_id,
        "user_id": str(user_id),
        "uid": str(uid),
        "likes_requested": int(likes_requested),
        "likes_sent": 0,
        "remaining_likes": int(likes_requested),
        "price": int(price),
        "region": FIXED_REGION,
        "status": "active",
        "created_at": bd_timestamp(),
        "started_at": bd_timestamp(),
        "last_run_at": None,
        "last_likes": 0,
        "last_note": "Order accepted; Auto Like scheduled.",
        "completed_at": None,
        "paid_at": None,
    }
    save_data("orders", orders)
    return orders[order_id]


def get_orders(user_id=None, limit=None):
    orders = load_data("orders")
    if not isinstance(orders, dict):
        return []
    items = list(orders.values())
    if user_id is not None:
        items = [x for x in items if str(x.get("user_id")) == str(user_id)]
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items[:limit] if limit else items


def get_order(order_id):
    orders = load_data("orders")
    return orders.get(str(order_id)) if isinstance(orders, dict) else None


def update_order(order_id, **changes):
    orders = load_data("orders")
    if not isinstance(orders, dict) or str(order_id) not in orders:
        return None
    orders[str(order_id)].update(changes)
    save_data("orders", orders)
    return orders[str(order_id)]


def format_eta(remaining_likes):
    remaining = max(0, int(remaining_likes or 0))
    if remaining <= 0:
        return "Complete"
    per_day = max(1, int(AUTO_LIKE_DAILY_ESTIMATE))
    days = (remaining + per_day - 1) // per_day
    if days < 30:
        return f"প্রায় {days} দিন"
    months = (days + 29) // 30
    return f"প্রায় {months} মাস ({days} দিন)"


def order_history_text(user_id, limit=10):
    orders = get_orders(user_id, limit=limit)
    if not orders:
        return "📜 ORDER HISTORY\n\nআপনার এখনো কোনো package order নেই।"
    lines = ["📜 AS LIKE BOT — ORDER HISTORY", "━━━━━━━━━━━━━━━━━━"]
    for o in orders:
        requested = int(o.get("likes_requested", 0))
        sent = int(o.get("likes_sent", 0))
        remaining = max(0, requested - sent)
        status = o.get("status", "active")
        status_map = {"active": "🟢 ACTIVE", "completed": "✅ COMPLETED", "cancelled": "🛑 CANCELLED", "payment_pending": "💳 PAYMENT PENDING"}
        lines += [
            f"🆔 Order: {o.get('order_id', 'N/A')}",
            f"🎮 UID: {o.get('uid', 'N/A')}",
            f"📦 Ordered: {requested:,} Likes",
            f"❤️ Sent: {sent:,} Likes",
            f"⏳ Remaining: {remaining:,} Likes",
            f"📅 ETA: {format_eta(remaining) if status == 'active' else '—'}",
            f"💳 Cost: {int(o.get('price', 0))} Points",
            f"📌 Status: {status_map.get(status, status.upper())}",
            f"🗓️ Order Date: {o.get('created_at', 'N/A')}",
            f"⏰ Last Run: {o.get('last_run_at') or 'Not started yet'}",
            f"ℹ️ {o.get('last_note') or '—'}",
            "━━━━━━━━━━━━━━━━━━",
        ]
    lines.append("📢 নোটিশ: Like stock কম থাকায় কোনো কোনো দিনে নির্ধারিত পরিমাণের চেয়ে কম Like যেতে পারে। Order চলাকালীন প্রতিদিন ভোর ৫:০০টার পর Auto Like চেষ্টা করা হবে।")
    return "\n".join(lines)


def classify_api_result(result):
    """Return a user-safe reason without exposing raw API errors."""
    if not isinstance(result, dict):
        return "temporary"
    raw = " ".join(str(result.get(k, "")) for k in ("error", "message", "reason", "detail", "status_message")).lower()
    if any(word in raw for word in ("europe", "india", "indonesia", "brazil", "singapore", "mena", "not bd", "wrong region", "invalid region", "unsupported region")):
        return "region"
    return "temporary"

def build_main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("💰 BALANCE"), KeyboardButton("💳 ADD MONEY")],
        [KeyboardButton("⭐ LIKE USE HISTORY")],
        [KeyboardButton("📜 ORDER HISTORY"), KeyboardButton("📦 AUTO LIKE PACKAGE")],
        [KeyboardButton("🚀 220 LIKE"), KeyboardButton("🎁 FREE LIKE 50")],
        [KeyboardButton("👻 REFER AND EARN")],
        [KeyboardButton("🆘 CUSTOMER CARE")],
    ], resize_keyboard=True)


def package_text():
    lines = [
        f"📦 {BOT_NAME} — AUTO LIKE PACKAGE",
        "",
        "আপনার পছন্দের package number select করুন:",
        "",
    ]
    for index, (likes, price) in enumerate(AUTO_LIKE_PACKAGES, start=1):
        lines.append(f"{index}. ❤️ {likes:,} Likes — {price} TK")
    lines += [
        "",
        "ℹ️ Package select করার পর আপনার Free Fire UID দিতে হবে।",
        "💰 Package-এর price আপনার bot balance থেকে কাটা হবে।",
    ]
    return "\n".join(lines)


def build_admin_contact_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 CONTACT ADMIN", url=ADMIN_URL)]
    ])


def build_package_keyboard():
    buttons = []
    for index, (likes, price) in enumerate(AUTO_LIKE_PACKAGES, start=1):
        buttons.append([
            InlineKeyboardButton(
                f"{index}. ❤️ {likes:,} Likes — {price} TK",
                callback_data=f"package_select_{index}"
            )
        ])
    buttons.append([InlineKeyboardButton("❌ CANCEL", callback_data="package_cancel")])
    return InlineKeyboardMarkup(buttons)


async def package_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select a package; no likes are sent and no balance is deducted at selection time."""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    ensure_user(user.id, user)
    data = query.data or ""

    if data == "package_cancel":
        context.user_data.pop("pending_package", None)
        await query.edit_message_text(format_bold("❌ Package order cancelled."), parse_mode=ParseMode.MARKDOWN)
        return
    if not data.startswith("package_select_"):
        return
    try:
        index = int(data.rsplit("_", 1)[1])
        likes, price = AUTO_LIKE_PACKAGES[index - 1]
    except (ValueError, IndexError):
        await query.edit_message_text(format_bold("❌ এই package আর available নেই। আবার package list খুলুন।"), parse_mode=ParseMode.MARKDOWN)
        return

    if likes in COMING_SOON_PACKAGES:
        context.user_data.pop("pending_package", None)
        await query.edit_message_text(format_bold(f"📦 {likes:,} LIKES\n\n🚧 COMING SOON!\n\nএই package এখনো চালু হয়নি।"), parse_mode=ParseMode.MARKDOWN)
        return

    balance = get_balance(user.id)
    if balance < price:
        context.user_data.pop("pending_package", None)
        await query.edit_message_text(format_bold(
            f"❌ পর্যাপ্ত Balance নেই!\n\n📦 Selected: {likes:,} Likes\n💳 Package Price: {price} Points\n💰 Your Balance: {balance} Points\n\nআগে Balance Add Money করে নিন।"
        ), parse_mode=ParseMode.MARKDOWN, reply_markup=build_admin_contact_keyboard())
        return

    context.user_data["pending_package"] = {"likes": likes, "price": price, "selected_at": bd_timestamp()}
    await query.edit_message_text(format_bold(
        f"✅ PACKAGE SELECTED\n━━━━━━━━━━━━━━━━━━\n📦 Package: {likes:,} Likes\n💳 Price: {price} Points\n💰 Current Balance: {balance} Points\n\n🎮 এখন আপনার BD Server Free Fire UID পাঠান:\nউদাহরণ: 123456789\n\n⚡ Order তৈরি হওয়ার পর UID-তে Auto Like চালু হবে।\n⏰ প্রতিদিন ভোর ৫:০০টার পর Like দেওয়ার চেষ্টা করা হবে।\n💳 Order পুরোপুরি complete না হওয়া পর্যন্ত কোনো Point কাটা হবে না।"
    ), parse_mode=ParseMode.MARKDOWN)


async def process_package_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a long-running auto-like order. No API call is made at order creation."""
    pending = context.user_data.get("pending_package")
    if not pending:
        return False
    user = update.effective_user
    uid = (update.message.text or "").strip()
    if not uid.isdigit():
        await update.message.reply_text(format_bold("❌ সঠিক Free Fire UID দিন।\n\nশুধু সংখ্যা দিন।"), parse_mode=ParseMode.MARKDOWN)
        return True

    likes_requested = int(pending.get("likes", 0))
    price = int(pending.get("price", 0))
    balance = get_balance(user.id)
    if likes_requested <= 0:
        context.user_data.pop("pending_package", None)
        await update.message.reply_text(format_bold("❌ Package configuration ভুল। Admin-কে জানান।"), parse_mode=ParseMode.MARKDOWN)
        return True
    if balance < price:
        context.user_data.pop("pending_package", None)
        await update.message.reply_text(format_bold(f"❌ আপনার Balance কম।\n\n💳 Required: {price} Points\n💰 Current Balance: {balance} Points"), parse_mode=ParseMode.MARKDOWN, reply_markup=build_admin_contact_keyboard())
        return True

    # Avoid duplicate active orders for the same UID.
    active = [o for o in get_orders(limit=None) if str(o.get("uid")) == uid and o.get("status") in ("active", "payment_pending")]
    if active:
        context.user_data.pop("pending_package", None)
        o = active[0]
        remaining = max(0, int(o.get("likes_requested", 0)) - int(o.get("likes_sent", 0)))
        await update.message.reply_text(format_bold(
            f"⚠️ এই UID-তে একটি active order already আছে।\n\n🆔 Order: {o.get('order_id')}\n🎮 UID: {uid}\n❤️ Sent: {o.get('likes_sent', 0):,}\n⏳ Remaining: {remaining:,}\n📅 ETA: {format_eta(remaining)}"
        ), parse_mode=ParseMode.MARKDOWN)
        return True

    order = create_order(user.id, uid, likes_requested, price)
    auto = load_data("auto_like")
    auto[uid] = {
        "region": FIXED_REGION,
        "days_left": max(3650, (likes_requested + max(1, AUTO_LIKE_DAILY_ESTIMATE) - 1) // max(1, AUTO_LIKE_DAILY_ESTIMATE) + 5),
        "added_at": bd_timestamp(),
        "order_id": order["order_id"],
        "order_mode": "package",
    }
    save_data("auto_like", auto)
    context.user_data.pop("pending_package", None)

    await update.message.reply_text(format_bold(
        f"🎉 ORDER CONFIRMED\n━━━━━━━━━━━━━━━━━━\n🆔 Order ID: {order['order_id']}\n🎮 UID: {uid}\n📦 Ordered: {likes_requested:,} Likes\n❤️ Sent: 0 Likes\n⏳ Remaining: {likes_requested:,} Likes\n📅 Estimated Time: {format_eta(likes_requested)}\n💳 Cost: {price} Points\n💰 Balance: {balance} Points\n\n🤖 Auto Like: ACTIVE\n⏰ প্রতিদিন ভোর ৫:০০টার পর Like দেওয়ার চেষ্টা হবে।\n\n💳 গুরুত্বপূর্ণ: Order সম্পূর্ণভাবে {likes_requested:,} Likes delivery হলে তবেই {price} Points আপনার Balance থেকে কাটা হবে। এর আগে কোনো Point কাটা হবে না।\n\n📢 NOTICE\nLike stock কম থাকায় কোনো কোনো দিনে Like কম যেতে পারে। তাই completion সময় কিছুটা বেশি হতে পারে।\n\n📜 Order History থেকে প্রতিদিন আপনার progress দেখতে পারবেন।"
    ), parse_mode=ParseMode.MARKDOWN)
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=format_bold(
            f"🆕 NEW PACKAGE ORDER\n\n🆔 {order['order_id']}\n👤 User: {user.id}\n🎮 UID: {uid}\n📦 {likes_requested:,} Likes\n💳 {price} Points\n⏰ Auto Like: 5:00 AM BD\n💰 Payment: ON COMPLETION"
        ), parse_mode=ParseMode.MARKDOWN)
    except Exception:
        logger.exception("Could not notify admin about order %s", order["order_id"])
    return True


async def menu_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (update.message.text or "").strip()
    ensure_user(user.id, user)
    add_broadcast_user(user.id)

    # A package UID is a stateful input, so handle it before normal menu text.
    if context.user_data.get("pending_package"):
        if text == "❌ CANCEL PACKAGE":
            context.user_data.pop("pending_package", None)
            await update.message.reply_text(
                format_bold("❌ Package order cancelled."),
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        if await process_package_uid(update, context):
            return

    if text == "💰 BALANCE":
        reply = (
            f"💰 {BOT_NAME} BALANCE\n\n"
            f"👤 User ID: {user.id}\n"
            f"💎 Available Points: {get_balance(user.id)}\n\n"
            f"➕ Point পেতে Refer & Earn ব্যবহার করুন।"
        )
        await update.message.reply_text(format_bold(reply), parse_mode=ParseMode.MARKDOWN)

    elif text == "💳 ADD MONEY":
        reply = (
            f"💳 ADD MONEY\n\n"
            f"Balance/Points নিতে Admin-এর সাথে Contact করুন।\n"
            f"আপনার User ID: {user.id}\n\n"
            f"নিচের বাটনে ক্লিক করে সরাসরি Admin-এর সাথে যোগাযোগ করুন।"
        )
        await update.message.reply_text(
            format_bold(reply),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_admin_contact_keyboard(),
        )

    elif text == "⭐ LIKE USE HISTORY":
        info = get_user_like_usage(user.id)
        reply = (
            f"⭐ {BOT_NAME} — LIKE USE HISTORY\n\n"
            f"👤 User ID: {user.id}\n"
            f"❤️ মোট পাওয়া Likes: {info['total_likes']}\n"
            f"📅 আজকে পাওয়া Likes: {info['today_likes']}\n"
            f"🔁 Successful Requests: {info['runs']}\n"
            f"➕ Last Request: {info['last_likes']} Likes"
        )
        await update.message.reply_text(format_bold(reply), parse_mode=ParseMode.MARKDOWN)

    elif text == "📜 ORDER HISTORY":
        await update.message.reply_text(format_bold(order_history_text(user.id, limit=10)), parse_mode=ParseMode.MARKDOWN)

    elif text == "🎟️ REDEEM CODES":
        await update.message.reply_text(
            format_bold(
                "🎟️ REDEEM CODES\n\n🚧 Coming Soon!\n\nRedeem Code System খুব শীঘ্রই চালু হবে."
            ),
            parse_mode=ParseMode.MARKDOWN,
        )

    elif text == "📦 AUTO LIKE PACKAGE":
        await update.message.reply_text(
            format_bold(package_text()),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_package_keyboard(),
        )

    elif text == "🚀 220 LIKE":
        await update.message.reply_text(
            format_bold(
                "🚀 220 LIKE\n\n🚧 Coming Soon!\n\nএই সার্ভিসটি বর্তমানে চালু নেই."
            ),
            parse_mode=ParseMode.MARKDOWN,
        )

    elif text == "🎁 FREE LIKE 50":
        await update.message.reply_text(
            format_bold(
                "🎁 FREE LIKE 50\n\n"
                "Free Like নিতে আপনার Free Fire UID দিয়ে command ব্যবহার করুন:\n\n"
                "/like <UID>\n\n"
                "উদাহরণ: /like 123456789\n\n"
                "📌 সাধারণ User প্রতিদিন ১ বার Free Like request করতে পারবেন."
            ),
            parse_mode=ParseMode.MARKDOWN,
        )

    elif text == "👻 REFER AND EARN":
        bot_username = (await context.bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start=ref_{user.id}"
        ref_stats = get_referral_stats(user.id)
        await update.message.reply_text(
            format_bold(
                f"👻 REFER AND EARN\n\n"
                f"প্রতি সফল নতুন referral-এ আপনি {REFERRAL_REWARD} Points পাবেন।\n\n"
                f"🔗 আপনার Referral Link:\n{referral_link}\n\n"
                f"💰 বর্তমান Balance: {get_balance(user.id)} Points\n"
                f"👥 মোট Referral: {ref_stats['count']} জন\n"
                f"🎁 Referral থেকে আয়: {ref_stats['earned']} Points"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )

    elif text == "🆘 CUSTOMER CARE":
        await update.message.reply_text(
            format_bold(
                "🆘 CUSTOMER CARE\n\n"
                "যেকোনো সমস্যা, Balance, Package বা সাহায্যের জন্য Admin-এর সাথে যোগাযোগ করুন."
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_admin_contact_keyboard(),
        )


async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the full admin control panel."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(format_bold("❌ Admin access only."), parse_mode=ParseMode.MARKDOWN)
        return
    users = load_data("users")
    referrals = load_data("referrals")
    text = (
        "👑 AS LIKE BOT — ADMIN PANEL\n\n"
        "👥 USER MANAGEMENT\n"
        "/users — সব bot user-এর Telegram ID দেখুন\n"
        "/user <id> — একজন user-এর details\n"
        "/addpoints <id> <points> — points দিন\n"
        "/setpoints <id> <points> — balance set করুন\n"
        "/vip <id> <days> — VIP দিন\n"
        "/vipremove <id> — VIP বাতিল\n"
        "/unlimit <uid> — UID unlimited করুন\n"
        "/removeunlimit <uid> — unlimited remove\n\n"
        "🎁 REFERRAL\n"
        "/refstats — referral statistics\n"
        "/setrefreward <points> — referral reward পরিবর্তন\n\n"
        "📦 LIKE / PACKAGE\n"
        "/packages — current package list\n"
        "/setpackage <likes> <price> — package add/update\n"
        "/editpackage <number> <likes> <price> — package edit\n"
        "/removepackage <likes> — package remove\n"
        "/autolike <uid> <days> — Auto Like\n"
        "/removeauto <uid> — Auto Like remove\n"
        "/autolist — Auto Like list\n"
        "/likeinfo <uid> — Like info\n"
        "/tlike <uid> <limit> — Target Like\n"
        "/removetlike <uid> — Target Like remove\n"
        "/tlist — Target Like list\n\n"
        "📜 ORDER MANAGEMENT\n"
        "/orders — সব package order\n"
        "/order <order_id> — order details\n"
        "/cancelorder <order_id> — order cancel\n"
        "/setdailyestimate <likes> — ETA estimate change\n\n"
        "📊 BOT CONTROL\n"
        "/stats — statistics\n"
        "/broadcast <message> — সবাইকে message\n"
        "/allow <group_id> / /removegroup <group_id>\n"
        "/add <name> <link> / /removechannel <name>\n"
        "/grouplist — allowed groups\n"
        "/on / /off — group bot control\n\n"
        f"📌 Registered Users: {len(users)}\n"
        f"🎁 Referral Records: {len(referrals)}\n"
        f"⚡ {BOT_NAME}"
    )
    await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)


async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(format_bold("❌ Admin access only."), parse_mode=ParseMode.MARKDOWN)
        return
    users = load_data("users")
    if not users:
        await update.message.reply_text(format_bold("👥 এখনো কোনো user registered নেই."), parse_mode=ParseMode.MARKDOWN)
        return
    lines = [f"👥 {BOT_NAME} USER LIST", f"Total: {len(users)}", ""]
    for uid, info in users.items():
        name = info.get("first_name", "Unknown")
        username = info.get("username", "")
        username_text = f"@{username}" if username else "No username"
        lines.append(f"🆔 {uid} | 👤 {name} | {username_text} | 💰 {info.get('balance', 0)} | 👥 Ref: {info.get('referrals', 0)}")
    await update.message.reply_text(format_bold("\n".join(lines)), parse_mode=ParseMode.MARKDOWN)


async def user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(format_bold("❌ Admin access only."), parse_mode=ParseMode.MARKDOWN)
        return
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text(format_bold("Format: /user <telegram_user_id>"), parse_mode=ParseMode.MARKDOWN)
        return
    uid = context.args[0]
    info = ensure_user(uid)
    ref = get_referral_stats(uid)
    usage = get_user_like_usage(uid)
    await update.message.reply_text(format_bold(
        f"👤 USER DETAILS\n\n🆔 ID: {uid}\n"
        f"👤 Name: {info.get('first_name', 'Unknown')}\n"
        f"🔗 Username: @{info.get('username')}\n" if info.get('username') else f"👤 USER DETAILS\n\n🆔 ID: {uid}\n👤 Name: {info.get('first_name', 'Unknown')}\n"
        f"💰 Balance: {info.get('balance', 0)} Points\n"
        f"👥 Referrals: {ref['count']}\n"
        f"🎁 Referral Earned: {ref['earned']} Points\n"
        f"❤️ Total Likes: {usage['total_likes']}\n"
        f"📅 Today Likes: {usage['today_likes']}"
    ), parse_mode=ParseMode.MARKDOWN)


async def refstats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(format_bold("❌ Admin access only."), parse_mode=ParseMode.MARKDOWN)
        return
    referrals = load_data("referrals")
    users = load_data("users")
    total_reward = sum(int(x.get("reward", 0)) for x in referrals.values())
    ranked = sorted(((uid, int(info.get("referrals", 0))) for uid, info in users.items()), key=lambda x: x[1], reverse=True)
    lines = ["🎁 REFERRAL STATISTICS", f"Total successful referrals: {len(referrals)}", f"Total points paid: {total_reward}", "", "🏆 Top Referrers:"]
    for uid, count in ranked[:20]:
        if count:
            lines.append(f"🆔 {uid} — {count} referrals")
    await update.message.reply_text(format_bold("\n".join(lines)), parse_mode=ParseMode.MARKDOWN)


async def setrefreward_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global REFERRAL_REWARD
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(format_bold("❌ Admin access only."), parse_mode=ParseMode.MARKDOWN)
        return
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text(format_bold("Format: /setrefreward <points>"), parse_mode=ParseMode.MARKDOWN)
        return
    REFERRAL_REWARD = int(context.args[0])
    await update.message.reply_text(format_bold(f"✅ Referral reward set to {REFERRAL_REWARD} Points."), parse_mode=ParseMode.MARKDOWN)


def package_admin_text():
    if not AUTO_LIKE_PACKAGES:
        return "📦 No packages configured."
    return "\n".join(
        f"{index}. 📦 {likes:,} Likes = {price} TK"
        for index, (likes, price) in enumerate(AUTO_LIKE_PACKAGES, start=1)
    )


async def packages_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(format_bold("❌ Admin access only."), parse_mode=ParseMode.MARKDOWN)
        return
    await update.message.reply_text(format_bold("📦 CURRENT PACKAGES\n\n" + package_admin_text() + "\n\n/setpackage <likes> <price>\n/removepackage <likes>"), parse_mode=ParseMode.MARKDOWN)


async def setpackage_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: add or update a package by its like amount."""
    global AUTO_LIKE_PACKAGES

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            format_bold("❌ Admin access only."),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if len(context.args) != 2 or not all(x.isdigit() for x in context.args):
        await update.message.reply_text(
            format_bold(
                "❌ Format:\n/setpackage <likes> <price>\n\n"
                "Example:\n/setpackage 500 25"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    likes, price = map(int, context.args)
    if likes <= 0 or price < 0:
        await update.message.reply_text(
            format_bold("❌ Likes অবশ্যই 0-এর বেশি এবং price 0 বা তার বেশি হতে হবে।"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    AUTO_LIKE_PACKAGES = [(l, p) for l, p in AUTO_LIKE_PACKAGES if l != likes]
    AUTO_LIKE_PACKAGES.append((likes, price))
    AUTO_LIKE_PACKAGES = save_packages(AUTO_LIKE_PACKAGES)

    await update.message.reply_text(
        format_bold(
            f"✅ Package saved!\n\n"
            f"❤️ Likes: {likes:,}\n"
            f"💳 Price: {price} TK\n\n"
            f"Restart করলেও এই package থাকবে।"
        ),
        parse_mode=ParseMode.MARKDOWN,
    )


async def editpackage_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: edit a package by its visible package number."""
    global AUTO_LIKE_PACKAGES

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            format_bold("❌ Admin access only."),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if len(context.args) != 3 or not all(x.isdigit() for x in context.args):
        await update.message.reply_text(
            format_bold(
                "❌ Format:\n/editpackage <number> <likes> <price>\n\n"
                "Example:\n/editpackage 1 100 5\n\n"
                "বর্তমান number দেখতে /packages ব্যবহার করুন।"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    index, likes, price = map(int, context.args)
    if index < 1 or index > len(AUTO_LIKE_PACKAGES) or likes <= 0 or price < 0:
        await update.message.reply_text(
            format_bold("❌ Package number/likes/price সঠিক নয়। /packages দিয়ে list দেখুন।"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    old_likes, _old_price = AUTO_LIKE_PACKAGES[index - 1]
    # Prevent duplicate like amounts after editing.
    if any(i != index - 1 and p[0] == likes for i, p in enumerate(AUTO_LIKE_PACKAGES)):
        await update.message.reply_text(
            format_bold("❌ এই Likes amount-এর package আগে থেকেই আছে।"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    AUTO_LIKE_PACKAGES[index - 1] = (likes, price)
    AUTO_LIKE_PACKAGES = save_packages(AUTO_LIKE_PACKAGES)

    await update.message.reply_text(
        format_bold(
            f"✅ Package edited successfully!\n\n"
            f"📌 Package No: {index}\n"
            f"🔄 Old Likes: {old_likes:,}\n"
            f"❤️ New Likes: {likes:,}\n"
            f"💳 New Price: {price} TK\n\n"
            f"User menu-তেও নতুন value দেখাবে।"
        ),
        parse_mode=ParseMode.MARKDOWN,
    )


async def removepackage_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: remove a package and persist the change."""
    global AUTO_LIKE_PACKAGES

    if not is_admin(update.effective_user.id):
        await update.message.reply_text(
            format_bold("❌ Admin access only."),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text(
            format_bold("Format: /removepackage <likes>"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    likes = int(context.args[0])
    before = len(AUTO_LIKE_PACKAGES)
    AUTO_LIKE_PACKAGES = [(l, p) for l, p in AUTO_LIKE_PACKAGES if l != likes]

    if len(AUTO_LIKE_PACKAGES) == before:
        msg = "❌ Package not found."
    else:
        AUTO_LIKE_PACKAGES = save_packages(AUTO_LIKE_PACKAGES)
        msg = f"✅ {likes:,} Likes package removed and saved."

    await update.message.reply_text(
        format_bold(msg),
        parse_mode=ParseMode.MARKDOWN,
    )


async def orderhistory_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(format_bold(order_history_text(user.id, limit=15)), parse_mode=ParseMode.MARKDOWN)


async def redeem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(format_bold("🎟️ REDEEM CODE\n\n🚧 COMING SOON!\n\nRedeem Code System খুব শীঘ্রই চালু হবে।"), parse_mode=ParseMode.MARKDOWN)


async def orders_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(format_bold("❌ Admin access only."), parse_mode=ParseMode.MARKDOWN)
        return
    orders = get_orders(limit=50)
    if not orders:
        await update.message.reply_text(format_bold("📜 কোনো order নেই।"), parse_mode=ParseMode.MARKDOWN)
        return
    lines = ["📜 ALL ORDERS — ADMIN", "━━━━━━━━━━━━━━━━━━"]
    for o in orders:
        requested = int(o.get("likes_requested", 0)); sent = int(o.get("likes_sent", 0)); remaining = max(0, requested-sent)
        lines.append(f"🆔 {o.get('order_id')} | 👤 {o.get('user_id')} | 🎮 {o.get('uid')} | ❤️ {sent:,}/{requested:,} | 📌 {o.get('status')} | ⏳ {format_eta(remaining)}")
    await update.message.reply_text(format_bold("\n".join(lines)), parse_mode=ParseMode.MARKDOWN)


async def order_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(format_bold("❌ Admin access only."), parse_mode=ParseMode.MARKDOWN)
        return
    if len(context.args) != 1:
        await update.message.reply_text(format_bold("Format: /order <order_id>"), parse_mode=ParseMode.MARKDOWN)
        return
    o = get_order(context.args[0])
    if not o:
        await update.message.reply_text(format_bold("❌ Order পাওয়া যায়নি।"), parse_mode=ParseMode.MARKDOWN)
        return
    requested = int(o.get("likes_requested", 0)); sent = int(o.get("likes_sent", 0)); remaining = max(0, requested-sent)
    await update.message.reply_text(format_bold(
        f"📦 ORDER DETAILS\n━━━━━━━━━━━━━━━━━━\n🆔 {o.get('order_id')}\n👤 User: {o.get('user_id')}\n🎮 UID: {o.get('uid')}\n📦 Ordered: {requested:,}\n❤️ Sent: {sent:,}\n⏳ Remaining: {remaining:,}\n📅 ETA: {format_eta(remaining)}\n💳 Price: {o.get('price', 0)} Points\n📌 Status: {o.get('status')}\n🗓️ Created: {o.get('created_at')}\n⏰ Last Run: {o.get('last_run_at') or 'N/A'}\nℹ️ {o.get('last_note') or 'N/A'}"
    ), parse_mode=ParseMode.MARKDOWN)


async def cancelorder_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(format_bold("❌ Admin access only."), parse_mode=ParseMode.MARKDOWN)
        return
    if len(context.args) != 1:
        await update.message.reply_text(format_bold("Format: /cancelorder <order_id>"), parse_mode=ParseMode.MARKDOWN)
        return
    order_id = context.args[0]
    o = get_order(order_id)
    if not o:
        await update.message.reply_text(format_bold("❌ Order পাওয়া যায়নি।"), parse_mode=ParseMode.MARKDOWN)
        return
    update_order(order_id, status="cancelled", last_note="Admin cancelled the order.", completed_at=bd_timestamp())
    auto = load_data("auto_like"); uid = str(o.get("uid"))
    if isinstance(auto, dict) and uid in auto and auto[uid].get("order_id") == order_id:
        auto.pop(uid, None); save_data("auto_like", auto)
    await update.message.reply_text(format_bold(f"🛑 Order {order_id} cancelled.\n💳 কোনো Point charge করা হয়নি।"), parse_mode=ParseMode.MARKDOWN)


async def setdailyestimate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AUTO_LIKE_DAILY_ESTIMATE
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(format_bold("❌ Admin access only."), parse_mode=ParseMode.MARKDOWN); return
    if len(context.args) != 1 or not context.args[0].isdigit() or int(context.args[0]) <= 0:
        await update.message.reply_text(format_bold("Format: /setdailyestimate <likes>\nExample: /setdailyestimate 100"), parse_mode=ParseMode.MARKDOWN); return
    AUTO_LIKE_DAILY_ESTIMATE = int(context.args[0])
    await update.message.reply_text(format_bold(f"✅ Daily estimate set to {AUTO_LIKE_DAILY_ESTIMATE} likes/day.\nনতুন order-এর ETA এতে হিসাব হবে।"), parse_mode=ParseMode.MARKDOWN)


async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(format_bold(
            f"💰 Your Balance: {get_balance(user.id)} Points"
        ), parse_mode=ParseMode.MARKDOWN)
        return
    await update.message.reply_text(format_bold(
        "💰 BALANCE ADMIN COMMANDS\n\n"
        "/addpoints <user_id> <points> — User-কে points দিন\n"
        "/setpoints <user_id> <points> — User-এর balance set করুন"
    ), parse_mode=ParseMode.MARKDOWN)


async def addpoints_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(format_bold("❌ You are not authorized!"), parse_mode=ParseMode.MARKDOWN)
        return
    if len(context.args) != 2 or not context.args[0].isdigit() or not context.args[1].lstrip("-").isdigit():
        await update.message.reply_text(format_bold(
            "❌ Format:\n/addpoints <telegram_user_id> <points>\nExample: /addpoints 123456789 50"
        ), parse_mode=ParseMode.MARKDOWN)
        return
    target, amount = context.args[0], int(context.args[1])
    new_balance = add_balance(target, amount)
    await update.message.reply_text(format_bold(
        f"✅ Points updated!\n\n👤 User: {target}\n➕ Change: {amount}\n💰 New Balance: {new_balance}"
    ), parse_mode=ParseMode.MARKDOWN)


async def setpoints_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text(format_bold("❌ You are not authorized!"), parse_mode=ParseMode.MARKDOWN)
        return
    if len(context.args) != 2 or not context.args[0].isdigit() or not context.args[1].isdigit():
        await update.message.reply_text(format_bold(
            "❌ Format:\n/setpoints <telegram_user_id> <points>"
        ), parse_mode=ParseMode.MARKDOWN)
        return
    target, amount = context.args[0], int(context.args[1])
    new_balance = set_balance(target, amount)
    await update.message.reply_text(format_bold(
        f"✅ Balance set successfully!\n\n👤 User: {target}\n💰 New Balance: {new_balance}"
    ), parse_mode=ParseMode.MARKDOWN)


# ═══════════════════════════════════════════════════════════════════
# FREE FIRE API CLIENT - UPDATED FOR NO KEY
# ═══════════════════════════════════════════════════════════════════

async def send_like_api(uid, region):
    """Call the API: https://aryan-shanto-fflikebot2-0.vercel.app/like?uid=3036489138&server_name=BD"""
    try:
        url = API_BASE.rstrip("/")
        params = {
            "uid": str(uid),
            "server_name": region.upper(),
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=25)) as resp:
                if resp.status != 200:
                    logger.error(f"API HTTP Error: Status code {resp.status}")
                    return {"error": "API is currently not working or returned invalid status.", "status": 0}
                
                data = await resp.json()
                return data
    except Exception as e:
        logger.error(f"Internal API Connection Error: {e}")
        return {"error": "API is currently not working or under maintenance.", "status": 0}


# ═══════════════════════════════════════════════════════════════════
# CHANNEL VERIFICATION
# ═══════════════════════════════════════════════════════════════════

async def check_channel_membership(user_id, context):
    """Check if user has joined all required channels"""
    channels = get_channels()
    if not channels:
        channels = {ch["name"]: {"link": ch["link"]} for ch in REQUIRED_CHANNELS}

    not_joined = []
    for name, info in channels.items():
        try:
            link = info.get("link", "")
            if "/" in link:
                parts = link.rstrip("/").split("/")
                username = parts[-1]
                if username.startswith("+"):
                    continue
                member = await context.bot.get_chat_member(f"@{username}", user_id)
                # Telegram can return member statuses: creator, administrator, member,
                # restricted, left, kicked. Restricted users are joined when is_member=True.
                if member.status in ["left", "kicked"] or (
                    member.status == "restricted" and not getattr(member, "is_member", False)
                ):
                    not_joined.append({"name": name, "link": link})
            else:
                not_joined.append({"name": name, "link": link})
        except Exception as e:
            logger.error(f"Channel check error for {name}: {e}")
            not_joined.append({"name": name, "link": info.get("link", "")})

    return not_joined


def build_verify_keyboard():
    """Build verification keyboard with channel buttons"""
    channels = get_channels()
    if not channels:
        channels = {ch["name"]: {"link": ch["link"]} for ch in REQUIRED_CHANNELS}

    buttons = []
    for name, info in channels.items():
        buttons.append([InlineKeyboardButton(f"📢 Join {name}", url=info["link"])])
    buttons.append([InlineKeyboardButton("✅ Verify", callback_data="verify_channels")])
    return InlineKeyboardMarkup(buttons)


# ═══════════════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    chat = update.effective_chat
    add_broadcast_user(user.id)
    ensure_user(user.id)

    referral_result = None
    if context.args:
        try:
            referral_result = process_referral(user.id, context.args[0])
        except Exception:
            logger.exception("Referral processing failed for user %s", user.id)

    emoji = get_user_emoji(user.id)
    text = (
        f"{emoji} WELCOME TO {BOT_NAME} {emoji}\n\n"
        f"👤 Name: {user.first_name}\n"
        f"🆔 ID: {user.id}\n"
        f"💰 Balance: {get_balance(user.id)} Points\n\n"
        f"🎮 Free Like নিতে: /like <UID>\n"
        f"📌 Example: /like 123456789\n\n"
        f"⚡ {BOT_NAME} ⚡"
    )
    if referral_result:
        text += (
            f"\n\n🎉 Referral Successful!\n"
            f"Referrer-কে {referral_result['reward']} Points যোগ হয়েছে।"
        )
        try:
            await context.bot.send_message(
                chat_id=referral_result["referrer"],
                text=format_bold(
                    f"🎉 REFERRAL SUCCESSFUL!\n\n"
                    f"👤 নতুন User: {user.first_name}\n"
                    f"🎁 Earned: +{referral_result['reward']} Points\n"
                    f"💰 New Balance: {referral_result['balance']} Points"
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            # The reward is already persisted; notification failure must never crash /start.
            logger.exception("Could not notify referrer %s", referral_result["referrer"])
    await update.message.reply_text(
        format_bold(text), parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_main_menu()
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command with distinct admin and user views"""
    user = update.effective_user
    chat = update.effective_chat
    add_broadcast_user(user.id)

    emoji = get_user_emoji(user.id)

    if is_admin(user.id):
        text = (
            f"{emoji} AS LIKE BOT - ADMIN PANEL {emoji}\n\n"
            f"🔐 Admin Commands:\n"
            f"/allow <group_id> - Allow bot in group\n"
            f"/removegroup <group_id> - Remove group\n"
            f"/add <name> <link> - Add verify channel\n"
            f"/removechannel <name> - Remove channel\n"
            f"/broadcast <message> - Message all users\n"            f"/addpoints <telegram_user_id> <points> - User-কে points দিন\n"
            f"/setpoints <telegram_user_id> <points> - User-এর balance set করুন\n"            
            f"/balance - Balance commands\n"
            f"/unlimit <uid> - Unlimited likes\n"
            f"/removeunlimit <uid> - Remove unlimited\n"
            f"/packages - Package list\n"
            f"/setpackage <likes> <price> - Add/update package\n"
            f"/editpackage <number> <likes> <price> - Edit package\n"
            f"/removepackage <likes> - Remove package\n"
            f"/vip <telegram_user_id> <days> - VIP দিন\n"
            f"/vipremove <telegram_user_id> - VIP বাতিল\n"
            f"/autolike <uid> <days> - Auto daily like\n"
            f"/removeauto <uid> - Remove auto like\n"
            f"/autolist - List auto-like UIDs\n"
            f"/likeinfo <uid> - Total/today likes info\n"
            f"/tlike <uid> <target_limit> - Daily like until target\n"
            f"/removetlike <uid> - Remove target like\n"
            f"/tlist - List target likes\n"
            f"/stats - Bot statistics\n"
            f"/grouplist - Allowed groups\n"
            f"/on - এই গ্রুপে bot চালু\n"
            f"/off - এই গ্রুপে bot বন্ধ\n\n"
            f"⚡ AS LIKE BOT ⚡"
        )
    else:
        text = (
            f"{emoji} AS LIKE BOT - USER MENU {emoji}\n\n"
            f"🎮 How to use:\n"
            f"/like <uid>\n"
            f"Example: /like 123456789\n\n"
            f"⚠️ Rules:\n"
            f"• সাধারণ ব্যবহারকারী প্রতিদিন ১ বার লাইক নিতে পারবেন\n"
            f"• VIP ব্যবহারকারীরা VIP সময়ের মধ্যে সীমাহীন লাইক নিতে পারবেন\n"
            f"• Reset at 4:00 AM daily\n"
            f"• Must join channels to use\n"
            f"• Bot works in allowed groups\n\n"
            f"⚡ AS LIKE BOT ⚡"
        )
    
    if not is_admin(user.id):
        vip_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 VIP নিতে Admin-এর সাথে Contact করুন", url="https://t.me/As_owner99")]
        ])
        await update.message.reply_text(
            format_bold(text),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=vip_button
        )
    else:
        await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)


async def like_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /like command - Works in Allowed or Pre-Authorized Groups"""
    user = update.effective_user
    chat = update.effective_chat
    add_broadcast_user(user.id)
    emoji = get_user_emoji(user.id)

    if chat.type in ["group", "supergroup"]:
        if not is_group_allowed(chat.id):
            text = (
                f"{emoji} AS LIKE BOT {emoji}\n\n"
                f"❌ This group is not authorized!\n"
                f"Contact admin to allow this group.\n\n"
                f"⚡ AS LIKE BOT ⚡"
            )
            await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)
            return
        if not is_group_enabled(chat.id) and not is_admin(user.id):
            text = (
                "❌ BOT IS OFF IN THIS GROUP!\n\n"
                "⚠️ একজন Group Admin /on দিলে আবার সবাই bot ব্যবহার করতে পারবে।\n\n"
                "👑 Admin: @As\\_owner99"
            )
            await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)
            return

    if len(context.args) < 1:
        text = (
            f"{emoji} সঠিকভাবে UID দিন {emoji}\n\n"
            f"🎮 লাইক নিতে ব্যবহার করুন:\n"
            f"/like <uid>\n\n"
            f"📌 উদাহরণ:\n"
            f"/like 123456789\n\n"
            f"⚡ AS LIKE BOT ⚡"
        )
        await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)
        return

    uid = context.args[0]
    region = FIXED_REGION

    # Check if the UID is already in Auto-Like or Target-Like lists
    auto_list = get_auto_like_list()
    targets = load_data("target_like")

    if uid in auto_list:
        days_left = auto_list[uid].get("days_left", 0)
        text = (
            f"❌ REQUEST REJECTED!\n\n"
            f"This UID already has an active Auto-Like setup.\n"
            f"📅 Remaining Duration: {days_left} Days\n"
            f"Likes are delivered automatically daily."
        )
        await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)
        return

    if uid in targets:
        likes_sent = targets[uid].get("likes_sent", 0)
        target_limit = targets[uid].get("target_limit", 0)
        text = (
            f"❌ REQUEST REJECTED!\n\n"
            f"This UID already has an active Target-Like setup.\n"
            f"📈 Current Progress: {likes_sent}/{target_limit} Likes\n"
            f"Likes are delivered automatically daily."
        )
        await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)
        return

    # Channel check
    not_joined = await check_channel_membership(user.id, context)
    if not_joined:
        text = (
            f"{emoji} VERIFICATION REQUIRED! {emoji}\n\n"
            f"❌ You must join all channels first!\n\n"
            f"📢 Join the channels below, then click Verify:"
        )
        await update.message.reply_text(
            format_bold(text),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_verify_keyboard(),
        )
        return

    if not is_unlimited(uid) and not can_use_like(user.id):
        text = (
            f"{emoji} দৈনিক লিমিট শেষ {emoji}\n\n"
            f"⚠️ আপনার আজকের লাইক নেওয়ার সীমা শেষ হয়ে গেছে।\n"
            f"🔄 প্রতিদিন ভোর ৪:০০টায় লিমিট পুনরায় চালু হবে।\n\n"
            f"💎 VIP হলে এই দৈনিক সীমা প্রযোজ্য নয়।\n"
            f"👑 Admin: @As\\_owner99\n\n"
            f"⚡ AS LIKE BOT ⚡"
        )
        await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)
        return

    processing_text = (
        f"{emoji} PROCESSING YOUR REQUEST... {emoji}\n\n"
        f"🎮 Player UID: {uid}\n"
        f"⏳ Please wait..."
    )
    msg = await update.message.reply_text(
        format_bold(processing_text), parse_mode=ParseMode.MARKDOWN
    )

    result = await send_like_api(uid, region)

    if result.get("error"):
        reason = classify_api_result(result)
        if reason == "region":
            error_text = (
                f"⚠️ BD SERVER REQUIRED\n\n"
                f"🎮 UID: {uid}\n"
                f"❌ এই UID-টি BD Server-এর নয় বলে Like দেওয়া যায়নি।\n\n"
                f"🇧🇩 অনুগ্রহ করে BD Server-এর Free Fire UID দিন।"
            )
        else:
            error_text = (
                f"⚠️ LIKE REQUEST FAILED\n\n"
                f"🎮 UID: {uid}\n"
                f"❌ Like service এই মুহূর্তে response দেয়নি।\n"
                f"🔄 ২৪ ঘণ্টা পরে আবার চেষ্টা করুন।"
            )
        await msg.edit_text(format_bold(error_text), parse_mode=ParseMode.MARKDOWN)
        return

    if result.get("status") in [1, 2] and int(result.get("LikesGivenByAPI", 0) or 0) > 0:
        player_name = result.get("PlayerNickname", "Unknown")
        likes_before = result.get("LikesbeforeCommand", "N/A")
        likes_after = result.get("LikesafterCommand", "N/A")
        likes_given = result.get("LikesGivenByAPI", 0)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        success_text = (
            f"✅ Like Sent Successfully!\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 Name: {player_name}\n"

            f"📉 Before: {likes_before}\n"
            f"📈 After: {likes_after}\n"
            f"➕ Given: {likes_given}\n"
            f"🆔 UID: {uid}\n"
            f"⏰ {current_time}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⚡ AS LIKE BOT ⚡"
        )

        if not is_unlimited(uid):
            mark_like_used(user.id)

        record_like_stats(uid, likes_given, source="manual")
        record_user_like_usage(user.id, likes_given)

        await msg.edit_text(format_bold(success_text), parse_mode=ParseMode.MARKDOWN)
    else:
        try:
            zero_likes = int(result.get("LikesGivenByAPI", 0) or 0) == 0
        except Exception:
            zero_likes = True
        if zero_likes:
            error_text = (
                f"⚠️ LIKE NOT SENT\n\n"
                f"🎮 UID: {uid}\n"
                f"❤️ Sent: 0 Likes\n\n"
                f"⚠️ আপনার আজকের Like limit শেষ হতে পারে।\n"
                f"🔄 ২৪ ঘণ্টা পরে আবার চেষ্টা করুন।"
            )
        else:
            error_text = f"⚠️ Like request complete হয়নি।\n\n🎮 UID: {uid}\n🔄 ২৪ ঘণ্টা পরে আবার চেষ্টা করুন।"
        await msg.edit_text(format_bold(error_text), parse_mode=ParseMode.MARKDOWN)


async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle verify button click"""
    query = update.callback_query
    await query.answer()
    user = query.from_user

    not_joined = await check_channel_membership(user.id, context)
    if not_joined:
        text = (
            f"❌ NOT VERIFIED!\n\n"
            f"You haven't joined all channels yet!\n"
            f"Join all channels first, then click Verify again."
        )
        await query.edit_message_text(
            format_bold(text),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_verify_keyboard(),
        )
    else:
        text = (
            f"✅ VERIFIED SUCCESSFULLY!\n\n"
            f"You can now use the bot!\n\n"
            f"Use /like <uid> to get likes"
        )
        await query.edit_message_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)


# ═══════════════════════════════════════════════════════════════════
async def _group_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE, enabled: bool):
    """Group-local admin toggle: /on or /off."""
    chat = update.effective_chat
    user = update.effective_user
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text(
            format_bold("❌ /on এবং /off শুধু গ্রুপে ব্যবহার করা যাবে।"),
            parse_mode=ParseMode.MARKDOWN
        )
        return

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status not in ["administrator", "creator"] and not is_admin(user.id):
            await update.message.reply_text(
                format_bold("❌ শুধু গ্রুপ Admin এই command ব্যবহার করতে পারবেন।"),
                parse_mode=ParseMode.MARKDOWN
            )
            return
    except Exception:
        await update.message.reply_text(
            format_bold("❌ আপনার Admin permission যাচাই করা যাচ্ছে না।"),
            parse_mode=ParseMode.MARKDOWN
        )
        return

    set_group_enabled(chat.id, enabled)
    text = (
        "✅ BOT ON\n\nএই গ্রুপে এখন সবাই /like ব্যবহার করতে পারবে।"
        if enabled else
        "🛑 BOT OFF\n\nএই গ্রুপে এখন সাধারণ user /like ব্যবহার করতে পারবে না।"
    )
    await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)


async def on_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _group_toggle(update, context, True)


async def off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _group_toggle(update, context, False)


# ADMIN COMMANDS
# ═══════════════════════════════════════════════════════════════════

async def allow_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /allow command"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(
            format_bold("❌ You are not authorized!"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if not context.args:
        text = (
            "❌ WRONG FORMAT!\n\n"
            "Correct: /allow <group_id>\n"
            "Example: /allow -1001234567890"
        )
        await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)
        return

    group_id = context.args[0]
    allow_group(group_id)
    text = (
        f"✅ GROUP ALLOWED!\n\n"
        f"Group ID: {group_id}\n"
        f"Bot will now work in this group!\n\n"
        f"⚡ AS LIKE BOT ⚡"
    )
    await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)


async def removegroup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /removegroup command"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(
            format_bold("❌ You are not authorized!"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if not context.args:
        text = "❌ Correct: /removegroup <group_id>"
        await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)
        return

    group_id = context.args[0]
    remove_group(group_id)
    text = (
        f"✅ Group {group_id} removed!\n\n"
        f"⚡ AS LIKE BOT ⚡"
    )
    await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)


async def addchannel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add command"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(
            format_bold("❌ You are not authorized!"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if len(context.args) < 2:
        text = (
            "❌ WRONG FORMAT!\n\n"
            "Correct: /add <button_name> <channel_link>\n"
            "Example: /add MyChannel https://t.me/mychannel"
        )
        await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)
        return

    name = context.args[0]
    link = context.args[1]
    add_channel(name, link)
    text = (
        f"✅ CHANNEL ADDED!\n\n"
        f"Name: {name}\n"
        f"Link: {link}\n\n"
        f"⚡ AS LIKE BOT ⚡"
    )
    await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)


async def removechannel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /removechannel command"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(
            format_bold("❌ You are not authorized!"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if not context.args:
        text = "❌ Correct: /removechannel <name>"
        await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)
        return

    name = context.args[0]
    remove_channel(name)
    text = (
        f"✅ Channel {name} removed!\n\n"
        f"⚡ AS LIKE BOT ⚡"
    )
    await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)


async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast command"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(
            format_bold("❌ You are not authorized!"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if not context.args:
        text = "❌ Correct: /broadcast <message>"
        await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)
        return

    message = " ".join(context.args)
    users = get_broadcast_users()
    sent = 0
    failed = 0

    status_msg = await update.message.reply_text(
        format_bold("📢 Broadcasting..."),
        parse_mode=ParseMode.MARKDOWN,
    )

    for uid in users:
        try:
            text = (
                f"📢 MESSAGE FROM ADMIN 📢\n\n"
                f"{message}\n\n"
                f"⚡ AS LIKE BOT ⚡"
            )
            await context.bot.send_message(
                uid, format_bold(text), parse_mode=ParseMode.MARKDOWN
            )
            sent += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            failed += 1
            logger.error(f"Broadcast failed for {uid}: {e}")

    text = (
        f"✅ BROADCAST COMPLETE!\n\n"
        f"Sent: {sent}\n"
        f"Failed: {failed}\n\n"
        f"⚡ AS LIKE BOT ⚡"
    )
    await status_msg.edit_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)


async def vip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only: /vip <telegram_user_id> <days>"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(format_bold("❌ You are not authorized!"), parse_mode=ParseMode.MARKDOWN)
        return
    if len(context.args) < 2:
        await update.message.reply_text(format_bold("❌ সঠিক ফরম্যাট:\n/vip <telegram_user_id> <days>\n\nউদাহরণ:\n/vip 15985683337 30"), parse_mode=ParseMode.MARKDOWN)
        return
    target_user_id, days = context.args[0], context.args[1]
    if not target_user_id.isdigit() or not days.isdigit() or int(days) <= 0:
        await update.message.reply_text(format_bold("❌ User ID এবং Days অবশ্যই সঠিক সংখ্যা হতে হবে।"), parse_mode=ParseMode.MARKDOWN)
        return
    add_vip(target_user_id, int(days))
    await update.message.reply_text(format_bold(f"✅ VIP সফলভাবে চালু হয়েছে!\n\n👤 Telegram ID: {target_user_id}\n📅 মেয়াদ: {days} দিন\n💎 এই সময়ের মধ্যে দৈনিক লিমিট প্রযোজ্য হবে না।"), parse_mode=ParseMode.MARKDOWN)


async def vipremove_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only: /vipremove <telegram_user_id>"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(format_bold("❌ You are not authorized!"), parse_mode=ParseMode.MARKDOWN)
        return
    if len(context.args) < 1:
        await update.message.reply_text(format_bold("❌ সঠিক ফরম্যাট:\n/vipremove <telegram_user_id>"), parse_mode=ParseMode.MARKDOWN)
        return
    target_user_id = context.args[0]
    if not target_user_id.isdigit():
        await update.message.reply_text(format_bold("❌ Telegram User ID অবশ্যই সংখ্যা হতে হবে।"), parse_mode=ParseMode.MARKDOWN)
        return
    remove_vip(target_user_id)
    await update.message.reply_text(format_bold(f"✅ VIP বাতিল করা হয়েছে।\n\n👤 Telegram ID: {target_user_id}"), parse_mode=ParseMode.MARKDOWN)


async def unlimit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unlimit command - fixed region"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(
            format_bold("❌ You are not authorized!"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if len(context.args) < 1:
        text = (
            "❌ WRONG FORMAT!\n\n"
            "Correct: /unlimit <uid>\n"
            "Example: /unlimit 15985683337"
        )
        await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)
        return

    uid = context.args[0]
    if not uid.isdigit():
        await update.message.reply_text(
            format_bold("❌ UID must be a number!"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    add_unlimited(uid, FIXED_REGION)
    text = (
        f"✅ UNLIMITED LIKE ADDED!\n\n"
        f"UID: {uid}\n"
        f"No daily limit for this UID!\n\n"
        f"⚡ AS LIKE BOT ⚡"
    )
    await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)


async def removeunlimit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /removeunlimit command"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(
            format_bold("❌ You are not authorized!"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if not context.args:
        text = "❌ Correct: /removeunlimit <uid>"
        await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)
        return

    uid = context.args[0]
    remove_unlimited(uid)
    text = (
        f"✅ UID {uid} removed from unlimited list!\n\n"
        f"⚡ AS LIKE BOT ⚡"
    )
    await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)


async def autolike_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /autolike command with format: /autolike <uid> <days>"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(
            format_bold("❌ You are not authorized!"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if len(context.args) < 2:
        text = (
            "❌ WRONG FORMAT!\n\n"
            "Correct: /autolike <uid> <days>\n"
            "Example: /autolike 15985683337 30"
        )
        await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)
        return

    uid = context.args[0]
    days = context.args[1]

    if not uid.isdigit() or not days.isdigit() or int(days) <= 0:
        await update.message.reply_text(
            format_bold("❌ UID and Days must be valid numbers!"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    add_auto_like(uid, FIXED_REGION, days)
    text = (
        f"✅ AUTO LIKE ADDED!\n\n"
        f"UID: {uid}\n"
        f"Duration: {days} Days\n"
        f"Daily like at 5:00 AM!\n\n"
        f"⚡ AS LIKE BOT ⚡"
    )
    await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)


async def removeauto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /removeauto command"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(
            format_bold("❌ You are not authorized!"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if not context.args:
        text = "❌ Correct: /removeauto <uid>"
        await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)
        return

    uid = context.args[0]
    remove_auto_like(uid)
    text = (
        f"✅ UID {uid} removed from auto-like list!\n\n"
        f"⚡ AS LIKE BOT ⚡"
    )
    await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)


async def likeinfo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only: show like statistics for a UID."""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(
            format_bold("❌ You are not authorized!"),
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            format_bold("❌ Correct: /likeinfo <uid>\nExample: /likeinfo 123456789"),
            parse_mode=ParseMode.MARKDOWN
        )
        return

    uid = context.args[0]
    stats = get_like_stats(uid)
    auto_info = get_auto_like_list().get(uid)
    target_info = load_data("target_like").get(uid)

    text = (
        f"📊 LIKE INFO\n\n"
        f"🆔 UID: {uid}\n"
        f"❤️ Total likes recorded: {stats['total_likes']}\n"
        f"📅 Today's likes: {stats['today_likes']}\n"
        f"🔁 Successful runs: {stats['runs']}\n"
        f"➕ Last run likes: {stats['last_likes']}\n"
    )

    if auto_info:
        text += (
            f"\n🤖 AUTO LIKE: ACTIVE\n"
            f"📆 Days left: {auto_info.get('days_left', 0)}\n"
            f"⏰ Schedule: 5:00 AM\n"
        )
    elif target_info:
        text += (
            f"\n🎯 TARGET LIKE: ACTIVE\n"
            f"📈 Progress: {target_info.get('likes_sent', 0)}/{target_info.get('target_limit', 0)}\n"
            f"⏰ Schedule: 5:00 AM\n"
        )
    else:
        text += "\nℹ️ No active Auto-Like/Target-Like setup for this UID.\n"

    text += "\n⚡ AS LIKE BOT ⚡"

    await update.message.reply_text(
        format_bold(text),
        parse_mode=ParseMode.MARKDOWN
    )


async def autolist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /autolist command"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(
            format_bold("❌ You are not authorized!"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    auto_list = get_auto_like_list()
    if not auto_list:
        text = "📋 Auto-like list is empty!"
    else:
        lines = ["📋 AUTO LIKE LIST:\n"]
        for uid, info in auto_list.items():
            lines.append(f"🆔 {uid} | 📅 Remaining: {info.get('days_left', 0)} Days")
        text = "\n".join(lines)
        text += "\n\n⚡ AS LIKE BOT ⚡"

    await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)


async def tlike_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /tlike command with format: /tlike <uid> <target_limit>"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(
            format_bold("❌ You are not authorized!"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if len(context.args) < 2:
        text = (
            "❌ WRONG FORMAT!\n\n"
            "Correct: /tlike <uid> <target_limit>\n"
            "Example: /tlike 15985683337 200"
        )
        await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)
        return

    uid = context.args[0]
    target_limit = context.args[1]

    if not uid.isdigit() or not target_limit.isdigit() or int(target_limit) <= 0:
        await update.message.reply_text(
            format_bold("❌ UID and Target Limit must be valid numbers!"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    add_target_like(uid, FIXED_REGION, target_limit)
    text = (
        f"✅ TARGET LIKE ADDED!\n\n"
        f"UID: {uid}\n"
        f"Target Limit: {target_limit} Likes\n"
        f"Will process daily at 5:00 AM until limit is reached!\n\n"
        f"⚡ AS LIKE BOT ⚡"
    )
    await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)


async def removetlike_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /removetlike command"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(
            format_bold("❌ You are not authorized!"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if not context.args:
        text = "❌ Correct: /removetlike <uid>"
        await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)
        return

    uid = context.args[0]
    remove_target_like(uid)
    text = (
        f"✅ UID {uid} removed from target-like list!\n\n"
        f"⚡ AS LIKE BOT ⚡"
    )
    await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)


async def tlist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /tlist command"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(
            format_bold("❌ You are not authorized!"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    targets = load_data("target_like")
    if not targets:
        text = "📋 Target-like list is empty!"
    else:
        lines = ["📋 TARGET LIKE LIST:\n"]
        for uid, info in targets.items():
            lines.append(f"🆔 {uid} | 📈 Progress: {info.get('likes_sent', 0)}/{info.get('target_limit', 0)}")
        text = "\n".join(lines)
        text += "\n\n⚡ AS LIKE BOT ⚡"

    await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(
            format_bold("❌ You are not authorized!"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    users = load_data("broadcast_users")
    groups = load_data("groups")
    channels = get_channels()
    auto_list = get_auto_like_list()
    targets = load_data("target_like")
    unlimited = load_data("unlimited")
    usage = load_data("daily_usage")

    text = (
        f"📊 BOT STATISTICS 📊\n\n"
        f"Total Users: {len(users)}\n"
        f"Today's Active: {len(usage)}\n"
        f"Allowed Groups: {len(groups)}\n"
        f"Channels: {len(channels)}\n"
        f"Auto-Like UIDs: {len(auto_list)}\n"
        f"Target-Like UIDs: {len(targets)}\n"
        f"Unlimited UIDs: {len(unlimited)}\n"
        f"VIP Users: {len(load_data('vip'))}\n\n"
        f"⚡ AS LIKE BOT ⚡"
    )
    await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)


async def grouplist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /grouplist command"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(
            format_bold("❌ You are not authorized!"),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    groups = load_data("groups")
    lines = ["📋 ALLOWED GROUPS:\n"]
    
    if PRE_AUTHORIZED_GROUPS:
        lines.append("⚙️ Pre-Authorized (From Code):")
        for gid in PRE_AUTHORIZED_GROUPS:
            lines.append(f"🆔 {gid}")
        lines.append("")

    if groups:
        lines.append("📝 Manually Allowed:")
        for gid, info in groups.items():
            lines.append(f"🆔 {gid}")
    
    if len(lines) == 1:
        text = "📋 No groups allowed yet!"
    else:
        text = "\n".join(lines)
        text += "\n\n⚡ AS LIKE BOT ⚡"

    await update.message.reply_text(format_bold(text), parse_mode=ParseMode.MARKDOWN)


# ═══════════════════════════════════════════════════════════════════
# SCHEDULER - Daily Reset & Auto Like
# ═══════════════════════════════════════════════════════════════════

async def run_daily_reset(application):
    """Reset daily usage at 4:00 AM"""
    while True:
        now = now_bd()
        target = now.replace(hour=RESET_HOUR, minute=RESET_MINUTE, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        wait_seconds = (target - now).total_seconds()
        logger.info(f"Next daily reset scheduled in {wait_seconds/3600:.1f} hours")
        await asyncio.sleep(wait_seconds)
        reset_daily_usage()


async def run_auto_like(application):
    """Reliable BD-time 05:00 scheduler for package Auto Like and legacy target/auto jobs."""
    while True:
        try:
            now = now_bd()
            target = now.replace(hour=AUTO_LIKE_HOUR, minute=AUTO_LIKE_MINUTE, second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)
            wait_seconds = max(1, (target - now).total_seconds())
            logger.info("Next auto-like run at %s (BD), in %.1f hours", target.isoformat(), wait_seconds/3600)
            await asyncio.sleep(wait_seconds)

            admin_report = ["📢 DAILY AUTO-LIKE REPORT", f"🗓️ {now_bd().strftime('%Y-%m-%d %H:%M:%S')} BD"]
            processed = 0; successful = 0; failed = 0
            orders = load_data("orders")
            if not isinstance(orders, dict): orders = {}
            auto_list = load_data("auto_like")
            if not isinstance(auto_list, dict): auto_list = {}

            # Package orders: one API call per active UID per day.
            for order_id, order in list(orders.items()):
                if order.get("status") not in ("active", "payment_pending"):
                    continue
                uid = str(order.get("uid"))
                remaining = max(0, int(order.get("likes_requested", 0)) - int(order.get("likes_sent", 0)))
                if remaining <= 0:
                    continue
                processed += 1
                result = await send_like_api(uid, FIXED_REGION)
                likes_given = 0
                try: likes_given = max(0, int(result.get("LikesGivenByAPI", 0) or 0))
                except Exception: likes_given = 0
                run_time = bd_timestamp()
                if result.get("status") in [1, 2] and likes_given > 0:
                    successful += 1
                    new_sent = min(int(order.get("likes_requested", 0)), int(order.get("likes_sent", 0)) + likes_given)
                    new_remaining = max(0, int(order.get("likes_requested", 0)) - new_sent)
                    update_order(order_id, likes_sent=new_sent, remaining_likes=new_remaining, last_run_at=run_time, last_likes=likes_given, last_note=f"আজ {likes_given:,} Likes delivered.")
                    record_like_stats(uid, likes_given, source="package_auto")
                    order["likes_sent"] = new_sent
                    order["remaining_likes"] = new_remaining
                    if new_remaining <= 0:
                        # Charge only after the complete requested amount has actually been delivered.
                        price = int(order.get("price", 0))
                        current_balance = get_balance(order.get("user_id"))
                        if current_balance >= price:
                            new_balance = add_balance(order.get("user_id"), -price)
                            update_order(order_id, status="completed", completed_at=run_time, paid_at=run_time, last_note=f"Order complete. {price} Points deducted.")
                            auto_list.pop(uid, None)
                            admin_report.append(f"✅ {order_id} | UID {uid} | COMPLETE | +{likes_given} | 💳 -{price} | Balance {new_balance}")
                            try:
                                await application.bot.send_message(chat_id=int(order.get("user_id")), text=format_bold(f"🎉 ORDER COMPLETED\n\n🆔 {order_id}\n🎮 UID: {uid}\n❤️ Total Sent: {new_sent:,} Likes\n💳 {price} Points সফলভাবে কাটা হয়েছে।\n💰 Remaining Balance: {new_balance} Points"), parse_mode=ParseMode.MARKDOWN)
                            except Exception: logger.exception("Could not notify user for completed order %s", order_id)
                        else:
                            update_order(order_id, status="payment_pending", completed_at=run_time, last_run_at=run_time, last_likes=likes_given, last_note=f"Likes complete, but balance {current_balance} is below {price} Points. Admin payment required.")
                            auto_list.pop(uid, None)
                            admin_report.append(f"⚠️ {order_id} | UID {uid} | LIKES COMPLETE | PAYMENT PENDING | Need {price}, balance {current_balance}")
                            try:
                                await application.bot.send_message(chat_id=int(order.get("user_id")), text=format_bold(f"⚠️ ORDER LIKES COMPLETED\n\n🆔 {order_id}\n🎮 UID: {uid}\n❤️ Total Sent: {new_sent:,} Likes\n💳 Package Cost: {price} Points\n\nআপনার বর্তমান Balance {current_balance} Points, তাই payment pending রাখা হয়েছে। Admin-এর সাথে যোগাযোগ করুন।"), parse_mode=ParseMode.MARKDOWN)
                            except Exception: logger.exception("Could not notify user about payment pending order %s", order_id)
                    else:
                        admin_report.append(f"✅ {order_id} | UID {uid} | +{likes_given} | Progress {new_sent}/{order.get('likes_requested')} | ETA {format_eta(new_remaining)}")
                else:
                    failed += 1
                    reason = classify_api_result(result)
                    if likes_given == 0 and reason == "region":
                        note = "BD Server UID নয় — BD Server-এর UID দিন।"
                    elif likes_given == 0:
                        note = "আজকের Like limit/stock শেষ হতে পারে; 24 hours পরে আবার চেষ্টা করা হবে।"
                    else:
                        note = "আজ Like পাঠানো যায়নি; পরের 24 hours cycle-এ আবার চেষ্টা হবে।"
                    update_order(order_id, last_run_at=run_time, last_likes=0, last_note=note)
                    admin_report.append(f"⚠️ {order_id} | UID {uid} | 0 Likes | {note}")
                await asyncio.sleep(2.0)

            # Legacy admin auto-like jobs remain supported.
            for uid, info in list(auto_list.items()):
                if info.get("order_id"):
                    continue
                days_left = int(info.get("days_left", 0) or 0)
                if days_left <= 0:
                    auto_list.pop(uid, None); continue
                result = await send_like_api(uid, FIXED_REGION)
                try: likes_given = max(0, int(result.get("LikesGivenByAPI", 0) or 0))
                except Exception: likes_given = 0
                if result.get("status") in [1, 2] and likes_given > 0:
                    info["days_left"] = days_left - 1
                    record_like_stats(uid, likes_given, source="auto")
                    successful += 1
                    admin_report.append(f"🤖 LEGACY AUTO | {uid} | +{likes_given} | Days Left {info['days_left']}")
                    if info["days_left"] <= 0: auto_list.pop(uid, None)
                    else: auto_list[uid] = info
                else:
                    failed += 1
                    admin_report.append(f"⚠️ LEGACY AUTO | {uid} | 0 Likes | next cycle retry")
                await asyncio.sleep(2.0)

            save_data("auto_like", auto_list)
            admin_report += ["", f"📊 Processed: {processed}", f"✅ Successful: {successful}", f"⚠️ Failed/0: {failed}", "⚡ AS LIKE BOT"]
            try:
                await application.bot.send_message(chat_id=ADMIN_ID, text=format_bold("\n".join(admin_report)), parse_mode=ParseMode.MARKDOWN)
            except Exception:
                logger.exception("Failed to send daily auto-like admin report")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Auto-like scheduler cycle failed; retrying tomorrow")
            await asyncio.sleep(30)


# ═══════════════════════════════════════════════════════════════════
# MAIN (Async Server Startup)
# ═══════════════════════════════════════════════════════════════════

async def main_async():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is empty. Put your Telegram bot token in BOT_TOKEN above.")
    # Build application
    application = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("like", like_cmd))
    application.add_handler(CommandHandler("orderhistory", orderhistory_cmd))
    application.add_handler(CommandHandler("redeem", redeem_cmd))
    application.add_handler(CommandHandler("on", on_cmd))
    application.add_handler(CommandHandler("off", off_cmd))

    # Admin commands
    application.add_handler(CommandHandler("allow", allow_cmd))
    application.add_handler(CommandHandler("removegroup", removegroup_cmd))
    application.add_handler(CommandHandler("add", addchannel_cmd))
    application.add_handler(CommandHandler("removechannel", removechannel_cmd))
    application.add_handler(CommandHandler("broadcast", broadcast_cmd))
    application.add_handler(CommandHandler("vip", vip_cmd))
    application.add_handler(CommandHandler("vipremove", vipremove_cmd))
    application.add_handler(CommandHandler("unlimit", unlimit_cmd))
    application.add_handler(CommandHandler("removeunlimit", removeunlimit_cmd))
    application.add_handler(CommandHandler("autolike", autolike_cmd))
    application.add_handler(CommandHandler("removeauto", removeauto_cmd))
    application.add_handler(CommandHandler("autolist", autolist_cmd))
    application.add_handler(CommandHandler("likeinfo", likeinfo_cmd))
    application.add_handler(CommandHandler("tlike", tlike_cmd))
    application.add_handler(CommandHandler("removetlike", removetlike_cmd))
    application.add_handler(CommandHandler("tlist", tlist_cmd))
    application.add_handler(CommandHandler("stats", stats_cmd))
    application.add_handler(CommandHandler("grouplist", grouplist_cmd))
    application.add_handler(CommandHandler("balance", balance_cmd))
    application.add_handler(CommandHandler("addpoints", addpoints_cmd))
    application.add_handler(CommandHandler("setpoints", setpoints_cmd))
    application.add_handler(CommandHandler("admin", admin_cmd))
    application.add_handler(CommandHandler("users", users_cmd))
    application.add_handler(CommandHandler("user", user_cmd))
    application.add_handler(CommandHandler("refstats", refstats_cmd))
    application.add_handler(CommandHandler("setrefreward", setrefreward_cmd))
    application.add_handler(CommandHandler("packages", packages_cmd))
    application.add_handler(CommandHandler("setpackage", setpackage_cmd))
    application.add_handler(CommandHandler("editpackage", editpackage_cmd))
    application.add_handler(CommandHandler("removepackage", removepackage_cmd))
    application.add_handler(CommandHandler("orders", orders_cmd))
    application.add_handler(CommandHandler("order", order_cmd))
    application.add_handler(CommandHandler("cancelorder", cancelorder_cmd))
    application.add_handler(CommandHandler("setdailyestimate", setdailyestimate_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_button_handler))

    # Callback handler
    application.add_handler(CallbackQueryHandler(verify_callback, pattern="^verify_channels$"))
    application.add_handler(CallbackQueryHandler(package_callback, pattern=r"^package_(select_\d+|cancel)$"))

    # Initialize and start Telegram Bot first. Starting background tasks before
    # the Telegram application is initialized can cause host/startup crashes.
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    scheduler_tasks = [
        asyncio.create_task(run_daily_reset(application), name="daily_reset"),
        asyncio.create_task(run_auto_like(application), name="auto_like"),
    ]
    logger.info("Background scheduler tasks started: %s", [t.get_name() for t in scheduler_tasks])
    logger.info("Telegram Bot polling started.")

    # Render Port Binding Setup
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Bot is running successfully!"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Port binding web server started on port {port}")

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        logger.info("Shutting down AS LIKE BOT...")
        for task in scheduler_tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*scheduler_tasks, return_exceptions=True)
        try:
            await application.updater.stop()
        except Exception:
            logger.exception("Error stopping Telegram updater")
        try:
            await application.stop()
        except Exception:
            logger.exception("Error stopping Telegram application")
        try:
            await application.shutdown()
        except Exception:
            logger.exception("Error shutting down Telegram application")
        try:
            await runner.cleanup()
        except Exception:
            logger.exception("Error cleaning up web server")


def main():
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║           AS LIKE BOT - Starting...                          ║
    ║           Free Fire Auto Like Bot                                ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
