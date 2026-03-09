import re
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, ContextTypes

# 启用日志记录，方便调试
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# 用于存储记录的列表
records = []
# 用于去重链接的集合
seen = set()

# 正则表达式：用于匹配 WhatsApp 群链接
pattern = r"https://chat\.whatsapp\.com/[A-Za-z0-9]+"

# 处理收到的消息
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.message.from_user.full_name  # 获取发送者名字
    text = update.message.text  # 获取发送的文本消息

    # 使用正则表达式提取消息中的 WhatsApp 群链接
    links = re.findall(pattern, text)

    for link in links:
        if link not in seen:  # 如果该链接尚未记录
            seen.add(link)
            records.append(f"{user} | {link}")  # 保存记录
            logging.info(f"记录：{user} | {link}")  # 输出日志，方便调试

# 处理 /export 命令，输出所有记录
async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not records:
        await update.message.reply_text("暂无记录")
        return

    result = "\n".join(records)  # 将记录列表转换为文本格式
    
    # 打印记录内容到控制台进行调试
    print("Exporting records:\n", result)
    
    # 发送导出的记录给用户
    await update.message.reply_text(result)

# 处理 /clear 命令，清空所有记录
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    records.clear()  # 清空记录列表
    seen.clear()  # 清空已记录链接的集合
    await update.message.reply_text("记录已清空")

# 设置 Telegram Bot 应用
app = ApplicationBuilder().token("你的BOT_TOKEN").build()

# 绑定处理函数
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))  # 处理群消息
app.add_handler(CommandHandler("export", export))  # 处理 /export 命令
app.add_handler(CommandHandler("clear", clear))  # 处理 /clear 命令

# 启动机器人
print("Bot running...")
app.run_polling()
