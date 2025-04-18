from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters
from telegram.error import BadRequest

from .helper_funcs.chat_status import user_admin
from .sql import chat_stats_sql as sql

def chat_stats(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    
    try:
        chat_members = chat.get_member_count()
    except BadRequest:
        chat_members = "Unknown"
        
    stats = f"""
📊 *Chat Statistics for {chat.title}*

👥 *Members:* {chat_members}
💬 *Total Messages:* {sql.get_chat_stats(chat.id).messages_count}
🆔 *Chat ID:* `{chat.id}`
📝 *Chat Type:* {chat.type}
    """
    
    if chat.username:
        stats += f"\n🔗 *Chat Username:* @{chat.username}"
        
    message.reply_text(stats, parse_mode=ParseMode.MARKDOWN)

def update_chat_stats(update: Update, context: CallbackContext):
    chat = update.effective_chat
    if not chat or chat.type == "private":
        return
        
    sql.update_chat_stats(chat.id) 