from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CommandHandler
from telegram.error import BadRequest, Unauthorized

from .helper_funcs.chat_status import user_admin
from .sql import connection_sql as sql

def connect(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    if update.effective_chat.type != "private":
        update.effective_message.reply_text("PM me with that command to connect to this chat!")
        return

    if not args or len(args) != 1:
        update.effective_message.reply_text("You need to give me a chat id to connect to!")
        return

    try:
        connect_chat = context.bot.get_chat(args[0])
        if connect_chat.type == 'private':
            update.effective_message.reply_text("I can't connect to private chats!")
            return
    except (BadRequest, Unauthorized):
        update.effective_message.reply_text("Invalid chat ID!")
        return

    sql.connect_chat(user.id, connect_chat.id)
    update.effective_message.reply_text(
        f"Successfully connected to *{connect_chat.title}*! "
        "You can now use admin commands as if you were in that chat.",
        parse_mode=ParseMode.MARKDOWN
    )

def disconnect(update: Update, context: CallbackContext):
    if update.effective_chat.type != "private":
        update.effective_message.reply_text("This command is only available in PM!")
        return

    sql.connect_chat(update.effective_user.id, None)
    update.effective_message.reply_text("Disconnected from chat!") 