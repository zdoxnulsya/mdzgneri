import os
import json
import asyncio
import aiohttp
import logging
from datetime import datetime

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
STEAM_API_KEY = os.environ.get('STEAM_API_KEY', '')

STEAM_ACCOUNTS = [
    ('76561199539034019', 'Aurora'),
    ('76561199528693162', 'EDP'),
    ('76561199170218093', 'Indra'),
    ('76561198828817873', 'Kali'),
    ('76561199166265130', 'Lindemann'),
    ('76561199069499409', 'Lucifer'),
    ('76561198150225815', 'Metal'),
    ('76561198959431750', 'Proc'),
    ('76561199276478180', 'Soul'),
    ('76561199559570410', 'Taiga')
]

DATA_FILE = 'friend_counts.json'
INIT_FILE = '.initialized'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SteamFriendMonitor")

async def fetch_friend_count(session, steam_id, name):
    url = f"http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key={STEAM_API_KEY}&steamid={steam_id}&relationship=friend"
    try:
        async with session.get(url, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                count = len(data.get('friendslist', {}).get('friends', []))
                return steam_id, name, count
            elif resp.status == 403:
                logger.warning(f"{name} is private")
                return steam_id, name, None
            else:
                logger.error(f"{name}: API error {resp.status}")
                return steam_id, name, None
    except Exception as e:
        logger.error(f"Error fetching {name}: {e}")
        return steam_id, name, None

async def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, data=payload) as resp:
                if resp.status != 200:
                    logger.error(f"Failed to send message: {await resp.text()}")
        except Exception as e:
            logger.error(f"Telegram error: {e}")

def load_previous_counts():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_counts(counts):
    with open(DATA_FILE, 'w') as f:
        json.dump(counts, f)

def is_first_run():
    if os.path.exists(INIT_FILE):
        return False
    with open(INIT_FILE, 'w') as f:
        f.write(datetime.now().isoformat())
    return True

async def check_accounts():
    first_run = is_first_run()
    previous = load_previous_counts()
    current = {}
    changes = []

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_friend_count(session, sid, name) for sid, name in STEAM_ACCOUNTS]
        results = await asyncio.gather(*tasks)

    for sid, name, count in results:
        if count is None:
            continue
        current[sid] = count
        prev_count = previous.get(sid)
        if prev_count is not None and not first_run:
            if count > prev_count:
                diff = count - prev_count
                msg = f"🎮 <b>New Friend Alert!</b>\n\n{name}: {prev_count} → {count}"
                await send_telegram_message(msg)
                changes.append(f"{name}: +{diff}")
            elif count < prev_count:
                diff = prev_count - count
                msg = f"❌ <b>Friend Removed</b>\n\n{name}: {prev_count} → {count}"
                await send_telegram_message(msg)
                changes.append(f"{name}: -{diff}")

    save_counts(current)

    if first_run:
        summary = "\n".join([f"• {name}: {current.get(sid, 'N/A')} friends" for sid, name in STEAM_ACCOUNTS])
        msg = f"📊 <b>Initial Summary</b>\n\n{summary}\n\n<i>Bot will now notify on changes only.</i>"
        await send_telegram_message(msg)
    elif changes:
        logger.info(f"Changes detected: {', '.join(changes)}")
    else:
        logger.info("No changes detected")

if __name__ == '__main__':
    asyncio.run(check_accounts())
