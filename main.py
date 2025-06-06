import os
if not os.path.exists("client.session"):
    raise FileNotFoundError("❌ client.session ফাইল পাওয়া যায়নি। GitHub Repo-তে এটি থাকতে হবে।")

import re
import gdown
import mimetypes
import threading
from aiogram import Bot, Dispatcher, executor, types
from pyrogram import Client
from flask import Flask, send_file
from googleapiclient.discovery import build
from google.oauth2 import service_account

# === CONFIG ===
BOT_TOKEN = "8039387061:AAGU8uaGE0iXREJJ_A0ePlaKY40EBEySibk"
API_ID = 27959473
API_HASH = "b4bd805185e65983cab8b214a33ef478"
PHONE_NUMBER = "+8801305977709"
CHANNEL_OR_GROUP = "@urluploaderx"
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === SETUP ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
pyro = Client("client", api_id=API_ID, api_hash=API_HASH, phone_number=PHONE_NUMBER)
app = Flask(__name__)

creds = service_account.Credentials.from_service_account_file("service_account_key.json")
drive_service = build('drive', 'v3', credentials=creds)

# === UTILITIES ===
def extract_drive_id(url):
    patterns = [
        r"file/d/([a-zA-Z0-9_-]+)",
        r"folders/([a-zA-Z0-9_-]+)",
        r"id=([a-zA-Z0-9_-]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def is_folder_link(url):
    return "/folders/" in url

def get_file_metadata(file_id):
    try:
        return drive_service.files().get(fileId=file_id, fields="name, mimeType").execute()
    except:
        return None

def list_folder_files(folder_id):
    files = []
    page_token = None
    while True:
        response = drive_service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=page_token
        ).execute()
        files.extend(response.get('files', []))
        page_token = response.get('nextPageToken')
        if not page_token:
            break
    return files

def build_filename(user_given, drive_name, mime):
    if user_given:
        return user_given
    ext = mimetypes.guess_extension(mime)
    if not ext and mime == "application/vnd.google-apps.document":
        ext = ".pdf"
    elif not ext:
        ext = ".bin"
    return f"{drive_name}{ext}" if not drive_name.endswith(ext) else drive_name

# === FLASK STREAM SERVER ===
@app.route('/stream/<file_id>')
def stream(file_id):
    for root, _, files in os.walk(DOWNLOAD_DIR):
        for file in files:
            if file_id in file:
                return send_file(os.path.join(root, file), as_attachment=True)
    return "File not found", 404

# === HANDLER ===
@dp.message_handler(lambda msg: "drive.google.com" in msg.text)
async def drive_handler(message: types.Message):
    links = re.findall(r"https?://drive.google.com[^\s]+", message.text)
    for link in links:
        file_id = extract_drive_id(link)
        if not file_id:
            await message.reply("❌ ফাইল আইডি পাওয়া যায়নি।")
            continue

        await message.reply("☁️ ডাউনলোড শুরু হচ্ছে.
" + link)

        if is_folder_link(link):
            folder_files = list_folder_files(file_id)
            folder_path = os.path.join(DOWNLOAD_DIR, file_id)
            os.makedirs(folder_path, exist_ok=True)
            for item in folder_files:
                filename = build_filename("", item["name"], item["mimeType"])
                dest_path = os.path.join(folder_path, filename)
                try:
                    gdown.download(f"https://drive.google.com/uc?id={item['id']}&export=download", dest_path, quiet=False)
                    size = os.path.getsize(dest_path)
                    if size > 50 * 1024 * 1024:
                        msg = await pyro.send_document(CHANNEL_OR_GROUP, dest_path)
                        await message.reply(f"🔗 বড় ফাইল এর chrome লিংক: (@urluploaderx এই গ্রুপে আপলোড করা) {filename}
https://telegram-drive-bot.onrender.com/stream/{msg.document.file_id}")
                    else:
                        await message.reply_document(dest_path)
                    os.remove(dest_path)
                except Exception as e:
                    await message.reply(f"❌ ডাউনলোডে সমস্যা: {str(e)}")
            continue

        metadata = get_file_metadata(file_id)
        if not metadata:
            await message.reply("❌ ফাইল ডিটেইলস পাওয়া যায়নি।")
            return

        user_filename_match = re.match(r"^(.*?)\s+https?://", message.text)
        user_filename = user_filename_match.group(1).strip() if user_filename_match else ""

        filename = build_filename(user_filename, metadata["name"], metadata["mimeType"])
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        try:
            gdown.download(f"https://drive.google.com/uc?id={file_id}&export=download", filepath, quiet=False)
            size = os.path.getsize(filepath)
            if size > 50 * 1024 * 1024:
                msg = await pyro.send_document(CHANNEL_OR_GROUP, filepath)
                await message.reply(f"🔗 বড় ফাইল এর chrome লিংক: (@urluploaderx এই গ্রুপে আপলোড করা) {filename}
https://telegram-drive-bot.onrender.com/stream/{msg.document.file_id}")
            else:
                await message.reply_document(filepath)
            os.remove(filepath)
        except Exception as e:
            await message.reply(f"❌ ডাউনলোডে সমস্যা: {str(e)}")

# === START ===
def run_server():
    app.run(host="0.0.0.0", port=3000)

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    pyro.start()
    executor.start_polling(dp, skip_updates=True)
