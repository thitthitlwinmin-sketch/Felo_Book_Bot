import os
import datetime
import json
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from flask import Flask
from threading import Thread

# --- Render အတွက် Web Server Setup ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Telegram Bot Logic ---
TOKEN = os.environ.get("BOT_TOKEN")


# Render Disk သုံးပြီး ဒေတာမပျောက်အောင် သိမ်းမည့်လမ်းကြောင်း
# အကယ်၍ Local စမ်းရင် books.txt အဖြစ်ပဲ သိမ်းသွားမည်
DATA_DIR = "/opt/render/project/src/data" if os.path.exists("/opt/render/project/src") else "."
os.makedirs(DATA_DIR, exist_ok=True)
DB_FILE = os.path.join(DATA_DIR, "books.txt")

def load_books():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_books(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        name = member.full_name
        now = datetime.datetime.now()
        time_str = now.strftime("%d.%m.%y %I:%M:%S %p %A")
        
        welcome_text = (
            f"🟢 - <b>{name}</b> ကို လူငယ်များgp& channel မှ ကြိုဆိုပါတယ်၊ မင်္ဂလာပါ။\n"
            f"<code>{member.id}</code> {time_str}"
        )
        await update.message.reply_text(welcome_text, parse_mode="HTML")

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if user_text.startswith('/add '):
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in ['creator', 'administrator']:
            await update.message.reply_text("❌ ဒီ Command ကို Admin များသာ Thသုံးနိုင်ပါသည်။")
            return
            
        raw_content = user_text[5:].strip()
        if "|" not in raw_content:
            await update.message.reply_text("❌ ပုံစံမမှန်ပါ။ ဥပမာ - <code>/add ဂျူး | အမှတ်တရ - လင့်ခ်</code> အတိုင်း ရိုက်ပေးပါ။", parse_mode="HTML")
            return
            
        author, book_info = raw_content.split("|", 1)
        author = author.strip()
        book_info = book_info.strip()
        
        books_db = load_books()
        if author in books_db:
            books_db[author] = books_db[author] + "\n" + book_info
        else:
            books_db[author] = f"<b>{author} စာအုပ်များ</b>\n\n" + book_info
            
        save_books(books_db)
        await update.message.reply_text(f"✅ စာရေးဆရာ <b>{author}</b> ရဲ့ စာအုပ်ကို Database ထဲ ထည့်သွင်းပြီးပါပြီ။", parse_mode="HTML")
        return

    if user_text.startswith('/'):
        command_name = user_text.split('@')[0].lstrip('/')
        books_db = load_books()
        
        if command_name in books_db:
            response = books_db[command_name]
            await update.message.reply_text(response, parse_mode="HTML")

def main():
    keep_alive()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    application.add_handler(MessageHandler(filters.TEXT, handle_messages))
    application.run_polling()

if __name__ == '__main__':
    main()
