import re
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, CallbackQueryHandler, ContextTypes

# 设置日志记录
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# 创建数据库连接（存储在项目目录）
conn = sqlite3.connect('whatsapp_links.db')  # SQLite 文件存储在项目目录
cursor = conn.cursor()

# 创建表格（如果表格已存在，则跳过创建）
cursor.execute('''
CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  # 添加 ID 字段，自动递增
    user TEXT,
    link TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP  # 添加时间戳
)
''')
conn.commit()

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
        if link in seen:  # 如果链接已经存在，提醒用户并跳过
            await update.message.reply_text(f"链接已经存在：{link}")
            continue
        
        # 如果是新链接，插入数据库并记录时间
        cursor.execute("INSERT INTO links (user, link) VALUES (?, ?)", (user, link))
        conn.commit()
        seen.add(link)  # 将链接添加到去重集合
        
        logging.info(f"记录：{user} | {link}")  # 输出日志，方便调试

        # 创建内联按钮
        keyboard = [
            [InlineKeyboardButton("导出链接", callback_data='export_links')],
            [InlineKeyboardButton("复制链接", callback_data='copy_links')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # 发送带有按钮的消息
        await update.message.reply_text(f"已记录: {user} | {link}", reply_markup=reply_markup)  # 给出反馈


# 处理按钮点击事件
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'export_links':
        # 从数据库获取所有记录，并按时间戳升序排序
        cursor.execute("SELECT user, link FROM links ORDER BY timestamp ASC")
        records = cursor.fetchall()

        if not records:
            await query.edit_message_text(text="暂无记录！")
            return

        # 显示所有链接并为每条链接添加删除按钮
        result = ""
        for user, link in records:
            result += f"{user} | {link}\n"
            # 创建删除按钮（将 ID 作为 callback_data）
            keyboard = [
                [InlineKeyboardButton("删除链接", callback_data=f'delete_{link}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # 发送每条记录，并附带删除按钮
            await query.edit_message_text(text=f"导出的链接:\n{result}", reply_markup=reply_markup)

    elif query.data.startswith('delete_'):
        link = query.data.split('_')[1]

        # 从数据库删除对应记录
        cursor.execute("DELETE FROM links WHERE link = ?", (link,))
        conn.commit()

        await query.edit_message_text(text="链接已删除！")

        # 更新记录
        await button(update, context)

# 创建清空链接按钮
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("确认清空链接", callback_data='confirm_clear_links')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text('你确定要清空所有链接吗？', reply_markup=reply_markup)

# 处理清空链接按钮点击事件
async def clear_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'confirm_clear_links':
        # 清空数据库中的记录
        cursor.execute("DELETE FROM links")
        conn.commit()
        await query.edit_message_text(text="所有链接已清空！")  # 更新消息文本

# 创建 /help 命令
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
    欢迎使用 WhatsApp 链接记录机器人！

    1. 发送 WhatsApp 群链接，机器人会自动记录并反馈。
    2. 点击“导出链接”按钮，可以查看所有记录的链接。
    3. 点击“复制所有链接”按钮，将显示所有链接，您可以复制它们。
    4. 输入 /clear 清空所有记录。
    5. 点击“确认清空链接”按钮，可以确认清空所有链接。
    6. 每条记录旁边有一个“删除链接”按钮，您可以删除单个链接。
    """
    await update.message.reply_text(help_text)

# 设置 Telegram Bot 应用
app = ApplicationBuilder().token("你的BOT_TOKEN").build()

# 绑定处理函数
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))  # 处理群消息
app.add_handler(CommandHandler("clear", clear))  # 处理 /clear 命令
app.add_handler(CommandHandler("help", help_command))  # 处理 /help 命令
app.add_handler(CallbackQueryHandler(button))  # 处理导出按钮点击事件
app.add_handler(CallbackQueryHandler(clear_button))  # 处理清空链接按钮点击事件

# 启动机器人
print("Bot running...")
app.run_polling()
