import threading
import os
import logging
import re
import sqlite3
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Bot active"

def run_flask():
    flask_app.run(host="0.0.0.0", port=5000)

conn = sqlite3.connect('whatsapp_links.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    link TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

seen = set()
pattern = r"https://chat\.whatsapp\.com/[A-Za-z0-9]+"

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.message.from_user.full_name
    text = update.message.text
    links = re.findall(pattern, text)

    for link in links:
        if link in seen:
            await update.message.reply_text(f"链接已经存在：{link}")
            continue

        cursor.execute("INSERT INTO links (user, link) VALUES (?, ?)", (user, link))
        conn.commit()
        seen.add(link)

        logging.info(f"记录：{user} | {link}")

        keyboard = [
            [InlineKeyboardButton("导出链接", callback_data='export_links')],
            [InlineKeyboardButton("复制链接", callback_data='copy_links')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"已记录: {user} | {link}", reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'export_links':
        cursor.execute("SELECT user, link FROM links ORDER BY user, timestamp ASC")
        records = cursor.fetchall()

        if not records:
            await query.edit_message_text(text="暂无记录！")
            return

        grouped_records = {}
        for user, link in records:
            if user not in grouped_records:
                grouped_records[user] = []
            grouped_records[user].append(link)

        result = ""
        for user, links in grouped_records.items():
            result += f"\n{user} 的群链接:\n"
            for link in links:
                result += f"{link}\n"

            keyboard = [
                [InlineKeyboardButton("删除链接", callback_data=f'delete_{user}_{link}')]
                for link in links
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=f"{result}", reply_markup=reply_markup)

    elif query.data.startswith('delete_'):
        parts = query.data.split('_')
        user = parts[1]
        link = parts[2]

        cursor.execute("DELETE FROM links WHERE user = ? AND link = ?", (user, link))
        conn.commit()

        await query.edit_message_text(text="链接已删除！")
        await button(update, context)


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("确认清空链接", callback_data='confirm_clear_links')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('你确定要清空所有链接吗？', reply_markup=reply_markup)


async def clear_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'confirm_clear_links':
        cursor.execute("DELETE FROM links")
        conn.commit()
        await query.edit_message_text(text="所有链接已清空！")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
    欢迎使用 WhatsApp 链接记录机器人！

    1. 发送 WhatsApp 群链接，机器人会自动记录并反馈。
    2. 点击"导出链接"按钮，可以查看所有记录的链接。
    3. 点击"复制所有链接"按钮，将显示所有链接，您可以复制它们。
    4. 输入 /clear 清空所有记录。
    5. 点击"确认清空链接"按钮，可以确认清空所有链接。
    6. 每条记录旁边有一个"删除链接"按钮，您可以删除单个链接。
    """
    await update.message.reply_text(help_text)


if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not TELEGRAM_BOT_TOKEN:
        logging.warning("TELEGRAM_BOT_TOKEN is not set. Bot will not connect to Telegram.")

    bot_app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    bot_app.add_handler(CommandHandler("clear", clear))
    bot_app.add_handler(CommandHandler("help", help_command))
    bot_app.add_handler(CallbackQueryHandler(button))
    bot_app.add_handler(CallbackQueryHandler(clear_button))

    print("Bot running...")
    bot_app.run_polling()
