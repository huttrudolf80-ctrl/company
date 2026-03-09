import re
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, ContextTypes

records = []
seen_links = set()

pattern = r"https://chat\.whatsapp\.com/[A-Za-z0-9]+"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message.text:
        return

    text = update.message.text
    user = update.message.from_user.full_name

    links = re.findall(pattern, text)

    for link in links:
        if link not in seen_links:
            seen_links.add(link)

            record = f"{user} | {link}"
            records.append(record)

            await update.message.reply_text("已记录")

async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not records:
        await update.message.reply_text("暂无记录")
        return

    result = "\n".join(records)

    await update.message.reply_text(result)

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):

    records.clear()
    seen_links.clear()

    await update.message.reply_text("记录已清空")

app = ApplicationBuilder().token("8413005679:AAHLbUiaMFjWm-nQtwKxIcliTyo5vZIkjZw").build()

app.add_handler(MessageHandler(filters.TEXT, handle_message))
app.add_handler(CommandHandler("export", export))
app.add_handler(CommandHandler("clear", clear))

print("bot running...")

app.run_polling()
