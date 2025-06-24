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

# Steam account IDs to monitor (just the IDs, no names needed)
STEAM_ACCOUNTS = [
    '76561199539034019',
    '76561199528693162',
    '76561199170218093',
    '76561198828817873',
    '76561199166265130',
    '76561199069499409',
    '76561198150225815',
    '76561198959431750',
    '76561199276478180',
    '76561199559570410'
]

DATA_FILE = 'friend_counts.json'
INIT_FILE = '.initialized'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SteamFriendMonitor")

def get_profile_link(steam_id):
    """Generate Steam profile link from Steam ID"""
    return f"steamcommunity.com/profiles/{steam_id}"

async def fetch_friend_count(session, steam_id):
    url = f"http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key={STEAM_API_KEY}&steamid={steam_id}&relationship=friend"
    profile_link = get_profile_link(steam_id)
    
    try:
        async with session.get(url, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                count = len(data.get('friendslist', {}).get('friends', []))
                return steam_id, profile_link, count
            elif resp.status == 403:
                logger.warning(f"{profile_link} is private")
                return steam_id, profile_link, None
            else:
                logger.error(f"{profile_link}: API error {resp.status}")
                return steam_id, profile_link, None
    except Exception as e:
        logger.error(f"Error fetching {profile_link}: {e}")
        return steam_id, profile_link, None

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
        tasks = [fetch_friend_count(session, steam_id) for steam_id in STEAM_ACCOUNTS]
        results = await asyncio.gather(*tasks)

    for steam_id, profile_link, count in results:
        if count is None:
            continue
        current[steam_id] = count
        prev_count = previous.get(steam_id)
        if prev_count is not None and not first_run:
            if count > prev_count:
                diff = count - prev_count
                msg = f"🎮 <b>New Friend Alert!</b>\n\n{profile_link}: {prev_count} → {count}"
                await send_telegram_message(msg)
                changes.append(f"{profile_link}: +{diff}")
            elif count < prev_count:
                diff = prev_count - count
                msg = f"❌ <b>Friend Removed</b>\n\n{profile_link}: {prev_count} → {count}"
                await send_telegram_message(msg)
                changes.append(f"{profile_link}: -{diff}")

    save_counts(current)

    if first_run:
        summary = "\n".join([f"• {get_profile_link(steam_id)}: {current.get(steam_id, 'N/A')} friends" 
                           for steam_id in STEAM_ACCOUNTS if steam_id in current])
        msg = f"📊 <b>Initial Summary</b>\n\n{summary}\n\n<i>Bot will now notify on changes only.</i>"
        await send_telegram_message(msg)
    elif changes:
        logger.info(f"Changes detected: {', '.join(changes)}")
    else:
        logger.info("No changes detected")

if __name__ == '__main__':
    asyncio.run(check_accounts())
