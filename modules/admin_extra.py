from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler
from telegram.error import BadRequest

from .helper_funcs.chat_status import user_admin, bot_admin

@bot_admin
@user_admin
def pin(update: Update, context: CallbackContext):
    args = context.args
    chat = update.effective_chat
    message = update.effective_message

    is_group = chat.type not in ("private", "channel")
    prev_message = update.effective_message.reply_to_message

    if not prev_message:
        message.reply_text("Reply to a message to pin it!")
        return

    is_silent = True if len(args) >= 1 and args[0].lower() == "notify" else False

    try:
        context.bot.pin_chat_message(
            chat.id, prev_message.message_id, disable_notification=is_silent
        )
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise

@bot_admin
@user_admin
def purge(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    
    if msg.reply_to_message:
        message_id = msg.reply_to_message.message_id
        delete_to = msg.message_id
        
        if message_id < 0:
            msg.reply_text("Cannot purge messages older than 48 hours.")
            return
            
        try:
            for m_id in range(message_id, delete_to + 1):
                try:
                    context.bot.delete_message(chat.id, m_id)
                except BadRequest:
                    pass
            msg.reply_text("Purge complete!")
        except BadRequest as err:
            msg.reply_text(f"Purge failed: {err.message}")
    else:
        msg.reply_text("Reply to a message to start purging from.") 