import random
import string
from typing import Optional

from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.error import BadRequest
from telegram.utils.helpers import mention_html

from .helper_funcs.chat_status import user_admin
from .sql import feds_sql as sql

def new_fed(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    
    if chat.type != "private":
        update.effective_message.reply_text("Federations can only be created by privately messaging me.")
        return
    
    if len(message.text.split()) < 2:
        update.effective_message.reply_text("Please write the name of the federation!")
        return
    
    fedname = message.text.split(None, 1)[1]
    if not fedname:
        update.effective_message.reply_text("Please write the name of the federation!")
        return

    fed_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Create federation
    sql.new_fed(user.id, fedname, fed_id)
    
    update.effective_message.reply_text(
        f"*Successfully created federation!*"
        f"\nName: `{fedname}`"
        f"\nID: `{fed_id}`"
        f"\n\nUse this ID to join the federation! For example:"
        f"\n`/joinfed {fed_id}`",
        parse_mode=ParseMode.MARKDOWN
    )

@user_admin
def join_fed(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    args = context.args
    
    if chat.type == 'private':
        update.effective_message.reply_text("This command is specific to groups, not our PM!")
        return
    
    if not args:
        update.effective_message.reply_text("Please enter the federation ID to join!")
        return
        
    fed_id = args[0]
    fed_info = sql.get_fed_info(fed_id)
    
    if not fed_info:
        update.effective_message.reply_text("This federation does not exist!")
        return
        
    sql.chat_join_fed(fed_id, chat.id)
    update.effective_message.reply_text(f"Successfully joined the federation: {fed_info['fname']}")

def fed_ban(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    args = context.args
    
    if chat.type == 'private':
        update.effective_message.reply_text("This command is specific to groups, not our PM!")
        return
        
    fed_id = sql.get_fed_id(chat.id)
    
    if not fed_id:
        update.effective_message.reply_text("This group is not part of any federation!")
        return
        
    if not sql.is_user_fed_admin(fed_id, user.id):
        update.effective_message.reply_text("Only federation admins can do this!")
        return
        
    if len(args) < 2:
        update.effective_message.reply_text("You seem to be trying to fban but haven't provided enough info!")
        return
        
    user_id = extract_user(message, args)
    if not user_id:
        update.effective_message.reply_text("You don't seem to be referring to a user.")
        return
        
    reason = " ".join(args[1:])
    
    # Execute ban
    sql.fban_user(fed_id, user_id, reason)
    
    # Ban user in all fed chats
    fed_chats = sql.all_fed_chats(fed_id)
    for chat_id in fed_chats:
        try:
            context.bot.ban_chat_member(chat_id, user_id)
        except BadRequest:
            continue
            
    update.effective_message.reply_text(
        f"User has been banned across all chats in this federation!\n"
        f"Reason: {reason}"
    ) 