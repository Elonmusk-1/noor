from typing import Optional

from telegram import Message, Chat, Update, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.utils.helpers import mention_html

from .helper_funcs.chat_status import user_admin, bot_admin
from .sql import locks_sql as sql

@bot_admin
@user_admin
def lock(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user

    if len(args) >= 1:
        lock_type = args[0].lower()
        
        if lock_type in ["sticker", "audio", "voice", "document", "video", "contact",
                        "photo", "url", "bots", "forward", "game", "location"]:
            
            # SQL
            sql.update_lock(chat.id, lock_type, locked=True)
            
            update.effective_message.reply_text(
                f"Locked {lock_type} for all non-admins!"
            )
            
            return f"<b>{html.escape(chat.title)}:</b>\n" \
                   f"#LOCK\n" \
                   f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n" \
                   f"Locked <code>{lock_type}</code>."
            
        else:
            update.effective_message.reply_text(
                "What are you trying to lock...? Try /locktypes for the list of lockables"
            )
            
    else:
        update.effective_message.reply_text("What are you trying to lock...?")

    return ""

@bot_admin
@user_admin
def unlock(update: Update, context: CallbackContext):
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    
    if len(args) >= 1:
        lock_type = args[0].lower()
        
        if lock_type in ["sticker", "audio", "voice", "document", "video", "contact",
                        "photo", "url", "bots", "forward", "game", "location"]:
            
            # SQL
            sql.update_lock(chat.id, lock_type, locked=False)
            
            update.effective_message.reply_text(
                f"Unlocked {lock_type} for everyone!"
            )
            
            return f"<b>{html.escape(chat.title)}:</b>\n" \
                   f"#UNLOCK\n" \
                   f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n" \
                   f"Unlocked <code>{lock_type}</code>."
            
        else:
            update.effective_message.reply_text(
                "What are you trying to unlock...? Try /locktypes for the list of lockables"
            )
            
    else:
        update.effective_message.reply_text("What are you trying to unlock...?")

    return "" 