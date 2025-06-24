import telebot
import os
import json
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = os.getenv("8111980313:AAEt-3mCkBQfe3LKHBGOKN_Z9tPovGlOTyM")
bot = telebot.TeleBot(API_TOKEN)
server = Flask(__name__)

ADMIN_ID = 1531380639  # Replace with your real Telegram user ID

def save_user(user):
    try:
        with open("data/users.json", "r+") as f:
            users = json.load(f)
            if user.id not in [u['id'] for u in users]:
                users.append({"id": user.id, "username": user.username})
                f.seek(0)
                json.dump(users, f, indent=4)
    except:
        pass

def save_file(file_info):
    try:
        with open("data/files.json", "r+") as f:
            files = json.load(f)
            files.append(file_info)
            f.seek(0)
            json.dump(files, f, indent=4)
    except:
        pass

@bot.message_handler(commands=['start'])
def start(message):
    save_user(message.from_user)
    bot.send_message(message.chat.id, "👋 Welcome! Send me a video/file and I'll generate a link for you.")

@bot.message_handler(commands=['panel'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "🚫 Access denied.")

    with open("data/users.json") as f: user_list = json.load(f)
    with open("data/files.json") as f: file_list = json.load(f)

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📬 Broadcast", callback_data="broadcast"),
        InlineKeyboardButton("📂 File Logs", callback_data="logs"),
        InlineKeyboardButton("♻ Refresh", callback_data="refresh_panel")
    )

    bot.send_message(
        message.chat.id,
        f"📊 Admin Control Panel\n\n👥 Users: {len(user_list)}\n📁 Files Shared: {len(file_list)}",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "refresh_panel")
def refresh_panel(call):
    class FakeMessage:
        def __init__(self, user_id):
            self.from_user = type("User", (), {"id": user_id})
            self.chat = type("Chat", (), {"id": user_id})
    admin_panel(FakeMessage(call.from_user.id))

@bot.message_handler(content_types=['document', 'video'])
def handle_file(message):
    save_user(message.from_user)

    file_data = message.document if message.document else message.video
    file_info = bot.get_file(file_data.file_id)
    file_path = file_info.file_path
    file_link = f"https://api.telegram.org/file/bot{8111980313:AAEt-3mCkBQfe3LKHBGOKN_Z9tPovGlOTyM}/{file_path}"

    file_name = file_data.file_name
    file_size_mb = round(file_data.file_size / (1024 * 1024), 2)
    watch_url = file_link

    save_file({
        "user_id": message.from_user.id,
        "file_name": file_name,
        "size": file_size_mb,
        "link": file_link
    })

    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("🎥 Online Watch", url=watch_url),
        InlineKeyboardButton("🌐 Open with Browser", url=file_link),
    )
    markup.add(
        InlineKeyboardButton("❌ Close", callback_data="close")
    )

    msg_text = (
        f"🐕 **Download Link Generated**\n\n"
        f"📁 **File Name:** `{file_name}`\n"
        f"💿 **Size:** `{file_size_mb} GiB`\n\n"
        f"🔗 **Link:** {file_link}\n"
        f"📥 **Online Watch:** {watch_url}\n\n"
        f"🤖 Bot By: [@SnakeEyeschannel65](https://t.me/SnakeEyeschannel65)"
    )

    bot.send_message(
        message.chat.id,
        msg_text,
        parse_mode="Markdown",
        reply_markup=markup,
        disable_web_page_preview=True
    )

@bot.callback_query_handler(func=lambda call: call.data == "close")
def handle_close(call):
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

@server.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"https://Files_Video_Link_Bot.onrender.com/{8111980313:AAEt-3mCkBQfe3LKHBGOKN_Z9tPovGlOTyM}")
    return "Webhook set!", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
