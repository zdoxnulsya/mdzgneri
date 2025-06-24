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
    
    '76561199419240292','76561199528974295','76561199418027556','76561199527942381','76561199418272921','76561199420987416','76561199416899795',
    '76561199430042714','76561199432208134','76561199404392645','76561199416330702','76561199528207164','76561199444883653','76561199527719299',
    '76561199418245374','76561199419478521','76561199528252168','76561199420619445','76561199434846406','76561199417492884','76561199418972285',
    '76561199419222699','76561199527844086','76561199417331887','76561199528104750','76561199417896406','76561199435031882','76561199417449874',
    '76561199418648313','76561199420296040','76561199434904088','76561199431267566','76561199528126727','76561199430053630','76561199417783633',
    '76561199432726503','76561199431286132','76561199419937468','76561199417586074','76561199433473782','76561199433508995','76561199528368811',
    '76561199419628572','76561199418134607','76561199527800632','76561199419325827','76561199433563059','76561199527611344','76561199420430794',
    '76561199418039488','76561199527396764','76561199417703947','76561199431758617','76561199434613423','76561199421315946','76561199528316816',
    '76561199433770220','76561199419040559','76561199431510092','76561199416386954','76561199444460905','76561199417703947','76561199420348905',
    '76561199419777845','76561199528324051','76561199404766318','76561199432979383','76561199418614186','76561199420066485','76561199434267626',
    '76561199433056341','76561199419550381','76561199417701336','76561199528886386','76561199434000454','76561199419058378','76561199527883112',
    '76561199528037890','76561199418107172','76561199528738484','76561199433216466','76561199444407752','76561199528046657','76561199432695506',
    '76561199416913404','76561199418155999','76561199419659927','76561199418107172','76561199528738484','76561199417660795','76561199433706551',
    '76561199434000454','76561199528689443','76561199434796124','76561199443818915','76561199431668090','76561199528407826','76561199418485509',
    '76561199420529526','76561199434619303','76561199419679089','76561199419690336','76561199528179319','76561199434327859','76561199417817156',
    '76561199417302243','76561199528523007','76561199444592159','76561199432986256','76561199444681000','76561199433553388','76561199527665527',
    '76561199433553388','76561199418041369','76561199527142067','76561199528113025','76561199432729789','76561199527946571','76561199420414495',
    '76561199418700318','76561199417765824','76561199444330870','76561199431649506','76561199416799410','76561199444068009','76561199404568031',
    '76561199430542827','76561199528767663','76561199418041369','76561199527946571','76561199419410856','76561199417162976','76561199444184678',
    '76561199527737182','76561199430165425','76561199528477677','76561199527287537','76561199429708232','76561199420598343','76561199528500358',
    '76561199430281304','76561199417046195','76561199434729654','76561199417888824','76561199418617278','76561199418336966','76561199528365163',
    '76561199404993033','76561199432847032','76561199433979540','76561199418479099','76561199417163062','76561199415983354','76561199528806801',
    '76561199433303998','76561199527989318','76561199417505038','76561199433542275','76561199528300767','76561199528052127','76561199528497800',
    '76561199418225012','76561199433107105','76561199419764677','76561199431856377','76561199443887021','76561199420378997','76561199432981955',
    '76561199417806467','76561199421502761','76561199528389664','76561199443791871','76561199528075461','76561199419027924',
    '76561199419627179','76561199528247910','76561199431721475','76561199419948293','76561199430048849','76561199421438640',
    '76561199433556206','76561199527853688','76561199417516244','76561199430183139','76561199419360519','76561199420819898',
    '76561199528725730','76561199528255589','76561199417804758','76561199528210792','76561199527112323','76561199418084035',
    '76561199417580242','76561199417230883','76561199417487625','76561199429545400','76561199528188514','76561199528046858',
    '76561199419026106','76561199419400066','76561199417580242','76561199418225012','76561199434085808','76561199418807171',
    '76561199419217264','76561199419607569','76561199527998449','76561199417381288','76561199528047369','76561199417196023',
    '76561199434364777','76561199528665392','76561199418980682','76561199527495560','76561199419728897','76561199421374395',
    '76561199528077087','76561199438498281','76561199528523573','76561199529078053','76561199528690266','76561199528133667',
    '76561199430417121','76561199417682963','76561199528480269','76561199527827460','76561199419109467','76561199528234752',
    '76561199418635996','76561199418826942','76561199431520867','76561199528783061','76561199417206517','76561199432483045',
    '76561199417960105','76561199528021054','76561199527912883','76561199417396660','76561199434206641','76561199418372202',
    '76561199419179098','76561199430657188','76561199527925976','76561199417279458','76561199430186675','76561199420065391',
    '76561199431743027','76561199434684790',
    
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
    """Send message to Telegram, splitting if too long"""
    MAX_MESSAGE_LENGTH = 4000  # Leave some buffer under 4096 limit
    
    if len(message) <= MAX_MESSAGE_LENGTH:
        await _send_single_message(message)
    else:
        # Split message into chunks
        lines = message.split('\n')
        current_chunk = ""
        
        for line in lines:
            # If adding this line would exceed limit, send current chunk
            if len(current_chunk + line + '\n') > MAX_MESSAGE_LENGTH:
                if current_chunk:
                    await _send_single_message(current_chunk.strip())
                    current_chunk = line + '\n'
                else:
                    # Single line is too long, truncate it
                    await _send_single_message(line[:MAX_MESSAGE_LENGTH])
            else:
                current_chunk += line + '\n'
        
        # Send remaining chunk
        if current_chunk:
            await _send_single_message(current_chunk.strip())

async def _send_single_message(message):
    """Send a single message to Telegram"""
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
                else:
                    logger.info("Telegram message sent successfully")
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
        # Send initial summary with account count
        total_accounts = len([steam_id for steam_id in STEAM_ACCOUNTS if steam_id in current])
        private_accounts = len(STEAM_ACCOUNTS) - total_accounts
        
        msg = f"📊 <b>Initial Setup Complete</b>\n\n"
        msg += f"✅ Monitoring {total_accounts} accounts\n"
        if private_accounts > 0:
            msg += f"🔒 {private_accounts} accounts are private\n"
        msg += f"\n<i>Bot will now notify on friend changes only.</i>"
        
        await send_telegram_message(msg)
        
        # Send detailed summary in smaller chunks if needed
        if total_accounts <= 50:  # Only send detailed list for smaller numbers
            summary = "\n".join([f"• {get_profile_link(steam_id)}: {current.get(steam_id, 'N/A')} friends" 
                               for steam_id in STEAM_ACCOUNTS if steam_id in current])
            detailed_msg = f"📋 <b>Account Details</b>\n\n{summary}"
            await send_telegram_message(detailed_msg)
    elif changes:
        logger.info(f"Changes detected: {', '.join(changes)}")
    else:
        logger.info("No changes detected")

if __name__ == '__main__':
    asyncio.run(check_accounts())
