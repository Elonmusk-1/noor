from telegram import Update, ChatPermissions, ParseMode
from telegram.ext import CallbackContext, MessageHandler, Filters, CommandHandler
from telegram.error import BadRequest
import time

from .helper_funcs.chat_status import bot_admin, user_admin
from .sql import antispam_sql as sql
from vars import Vars

SPAM_CHECK_GROUP = 15

@bot_admin
@user_admin
def free_user(update: Update, context: CallbackContext) -> None:
    """Free a user from anti-spam checks"""
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    
    if not args:
        message.reply_text("You need to specify a user!")
        return
        
    try:
        user_id = int(args[0])
    except ValueError:
        message.reply_text("Please provide a valid user ID!")
        return
        
    sql.set_exempt(chat.id, user_id, True)
    message.reply_text(f"User {user_id} is now exempt from anti-spam checks in this chat.")

@bot_admin
def check_spam(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    
    if not user or not chat:
        return
        
    # Don't check admins
    if user.id in context.bot_data.get('admin_list', []):
        return
        
    # Check if user is spamming
    if sql.check_spam(chat.id, user.id):
        try:
            # Restrict user
            context.bot.restrict_chat_member(
                chat.id,
                user.id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False
                ),
                until_date=int(time.time() + Vars.SPAM_MUTE_TIME)
            )
            
            msg.reply_text(
                f"❗️ Anti-spam system activated\n"
                f"User {user.mention_html()} has been muted for {Vars.SPAM_MUTE_TIME} seconds due to spamming.",
                parse_mode=ParseMode.HTML
            )
            
        except BadRequest as excp:
            msg.reply_text(f"Error: {excp.message}") 