# m3.py (Debouncing Logic Version)

import asyncio
import random
from telethon import TelegramClient, events
from telethon.errors.rpcerrorlist import FloodWaitError, UserBannedInChannelError, ChatWriteForbiddenError

# --- Account 1 Credentials ---
api_id_1 = 
api_hash_1 = ''
session_name_1 = 'session_account_1'

# --- Account 2 Credentials ---
api_id_2 = 
api_hash_2 = ''
session_name_2 = 'session_account_2'

# --- List of public group usernames to monitor ---
group_usernames = [
    'Acs_Udvash_Link', 'buetkuetruetcuet', 'linkedstudies', 'thejournyofhsc24',
    'hsc_sharing', 'ACSDISCUSSION', 'HHEHRETW', 'chemistryteli', 'haters_hsc',
    'hsc234', 'studywar2021', 'DiscussionGroupEngineering', 'Dacs2025', 'superb1k',
]

# --- Path to your image ---
image_path = 'Replit.jpg'

# --- The message to be sent ---
message_to_send = """
**🎓 ছাত্রজীবনের জন্য ৫টি কার্যকর টেলিগ্রাম চ্যানেল – একসাথে এক জায়গায়!**


1️⃣ **HSC গাইডলাইন, সাজেশন ও ২৪/৭ সাপোর্ট –**
     @guildline01

2️⃣ **ফ্রি টাইমে মোবাইল দিয়েই ইনকাম শেখো –**            
      @EarnovaX

3️⃣ **Class + Note + Guide PDF:**
     @PDFNexus

4️⃣ **প্রতি Gmail বিক্রি করে আয় করো 12 টাকা** –
🔗 https://t.me/GmailFarmerBot?start=7647683104

5️⃣ Spoken English Zone 🇬🇧
Spoken English, Grammar, Vocabulary ও IELTS শেখো বাংলায় সহজভাবে।
🎯 ইংরেজি শেখার পারফেক্ট বাংলা চ্যানেল –
👉 [Join Now](https://t.me/Spoken_English_Zone)
"""

# --- Initialize clients ---
client1 = TelegramClient(session_name_1, api_id_1, api_hash_1)
client2 = TelegramClient(session_name_2, api_id_2, api_hash_2)

clients = [client1, client2]
bot_ids = set()
active_client_index = 0

# --- নতুন পরিবর্তন: Debouncing এর জন্য ভ্যারিয়েবল ---
# প্রতিটি গ্রুপের জন্য আলাদা টাইমার টাস্ক সংরক্ষণ করার জন্য একটি ডিকশনারি
debounce_tasks = {}
# কতক্ষণ কোনো মেসেজ না আসলে বিজ্ঞাপন পাঠানো হবে (সেকেন্ডে)
DEBOUNCE_DELAY = 10  # ২০ সেকেন্ডের নীরবতার পর মেসেজ পাঠানো হবে

# --- নতুন পরিবর্তন: মেসেজ পাঠানোর জন্য আলাদা ফাংশন ---
async def send_promotional_message(chat_id, chat_title):
    """
    এই ফাংশনটি বিজ্ঞাপন পাঠানোর মূল কাজটি করে।
    """
    global active_client_index
    
    active_client = clients[active_client_index]
    client_number = active_client_index + 1

    try:
        print(f"✅ Silence period of {DEBOUNCE_DELAY}s ended for '{chat_title}'. Sending message now...")
        await active_client.send_message(
            chat_id,
            message_to_send,
            file=image_path,
            parse_mode='md'
        )
        print(f"✔️ Message with image successfully sent to '{chat_title}' by Client {client_number}.")

        # পরবর্তী মেসেজের জন্য ক্লায়েন্ট পরিবর্তন
        active_client_index = (active_client_index + 1) % len(clients)
        print(f"--> Switched active account. Next message will be from Client {active_client_index + 1}.\n")

    except FileNotFoundError:
        print(f"ERROR: Image file not found at '{image_path}'.")
    except (ChatWriteForbiddenError, UserBannedInChannelError):
        print(f"❌ Client {client_number} cannot post in '{chat_title}' (banned or permissions error).")
    except FloodWaitError as e:
        print(f"⚠️ Flood wait error for Client {client_number}. Waiting for {e.seconds} seconds.")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        print(f"An unexpected error occurred with Client {client_number} while sending to {chat_title}: {e}")
    finally:
        # টাস্ক শেষ হলে ডিকশনারি থেকে মুছে ফেলা হয়
        if chat_id in debounce_tasks:
            del debounce_tasks[chat_id]


@client1.on(events.NewMessage(chats=group_usernames))
async def main_handler(event):
    """
    এই ফাংশনটি প্রতিটি নতুন মেসেজে ট্রিগার হয় এবং শুধুমাত্র টাইমার রিসেট করার কাজ করে।
    """
    # নিজের পাঠানো মেসেজ উপেক্ষা করা
    if event.message.sender_id in bot_ids:
        return

    chat_id = event.chat_id
    
    # --- নতুন পরিবর্তন: Debouncing লজিক ---
    # ১. এই গ্রুপের জন্য যদি আগে থেকেই কোনো টাইমার চালু থাকে, তবে সেটি বাতিল করুন।
    if chat_id in debounce_tasks:
        debounce_tasks[chat_id].cancel()

    # ২. একটি নতুন টাইমার টাস্ক তৈরি করুন এবং সেটি ডিকশনারিতে সংরক্ষণ করুন।
    # DEBOUNCE_DELAY সেকেন্ড পর send_promotional_message ফাংশনটি চালানো হবে।
    async def schedule_send():
        try:
            await asyncio.sleep(DEBOUNCE_DELAY)
            await send_promotional_message(chat_id, event.chat.title)
        except asyncio.CancelledError:
            # যখন টাইমার রিসেট হয়, তখন এটি স্বাভাবিক
            print(f"Debounce timer reset for '{event.chat.title}' due to new activity.")
            # ব্যতিক্রমটি পুনরায় উত্থাপন করুন যাতে টাস্কটি সঠিকভাবে বন্ধ হয়
            raise

    print(f"New activity in '{event.chat.title}'. Waiting for {DEBOUNCE_DELAY}s of silence...")
    debounce_tasks[chat_id] = asyncio.create_task(schedule_send())


async def main():
    print("Connecting clients...")
    await client1.start()
    print("✅ Client 1 connected successfully.")
    await client2.start()
    print("✅ Client 2 connected successfully.")
    
    bot_ids.add((await client1.get_me()).id)
    bot_ids.add((await client2.get_me()).id)

    print("-------------------------------------------------")
    print(f"Bot is now monitoring {len(group_usernames)} groups with Debounce logic.")
    print(f"Will post a message after {DEBOUNCE_DELAY} seconds of inactivity in a group.")
    print("Waiting for new messages...")

    await client1.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        print(f"🛑 A critical error occurred in the main loop: {e}")
