
import telebot
import os
import json
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = os.getenv("API_TOKEN")
bot = telebot.TeleBot(API_TOKEN)
server = Flask(__name__)

ADMIN_ID = 1531380639

os.makedirs("data", exist_ok=True)
for filename in ["data/users.json", "data/files.json"]:
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            json.dump([], f)

def save_user(user):
    try:
        with open("data/users.json", "r+") as f:
            users = json.load(f)
            if user.id not in [u['id'] for u in users]:
                users.append({"id": user.id, "username": user.username})
                f.seek(0)
                json.dump(users, f, indent=4)
    except Exception as e:
        print("Error saving user:", e)

def save_file(file_info):
    try:
        with open("data/files.json", "r+") as f:
            files = json.load(f)
            files.append(file_info)
            f.seek(0)
            json.dump(files, f, indent=4)
    except Exception as e:
        print("Error saving file:", e)

@bot.message_handler(commands=['start'])
def start(message):
    save_user(message.from_user)
    bot.send_message(message.chat.id, "👋 Welcome! Send me a file or video and I’ll give you a download link.")

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
        f"📊 Admin Panel\n\n👥 Users: {len(user_list)}\n📁 Files: {len(file_list)}",
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
    file_link = f"https://api.telegram.org/file/bot{API_TOKEN}/{file_path}"

    file_name = file_data.file_name
    file_size_mb = round(file_data.file_size / (1024 * 1024), 2)

    save_file({
        "user_id": message.from_user.id,
        "file_name": file_name,
        "size": file_size_mb,
        "link": file_link
    })

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🎥 Watch Online", url=file_link),
        InlineKeyboardButton("🌐 Open Link", url=file_link),
        InlineKeyboardButton("❌ Close", callback_data="close")
    )

    msg_text = (
        f"📁 *File Name:* `{file_name}`\n"
        f"💾 *Size:* `{file_size_mb} MB`\n"
        f"🔗 *Link:* [Click to Download]({file_link})\n\n"
        f"🤖 Bot by [@SnakeEyeschannel65](https://t.me/SnakeEyeschannel65)"
    )

    bot.send_message(
        message.chat.id,
        msg_text,
        parse_mode="Markdown",
        reply_markup=markup,
        disable_web_page_preview=True
    )

@bot.callback_query_handler(func=lambda call: call.data == "close")
def close_msg(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

@server.route('/' + API_TOKEN, methods=['POST'])
def webhook_update():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return 'ok', 200

@server.route('/')
def set_webhook():
    webhook_url = f"https://{os.environ.get('HEROKU_APP_NAME')}.herokuapp.com/{API_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    return "Webhook Set!", 200

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
