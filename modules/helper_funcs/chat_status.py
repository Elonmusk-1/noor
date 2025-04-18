from functools import wraps
from telegram import Update, Chat, ChatMember, User
from telegram.ext import CallbackContext

from config import Config
from vars import Vars

from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

def is_user_admin(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    if chat.type == "private" or user_id in Config.DRAGONS:
        return True

    if not member:
        member = chat.get_member(user_id)

    return member.status in ("administrator", "creator")

def is_bot_admin(chat: Chat, bot_id: int, bot_member: ChatMember = None) -> bool:
    if chat.type == "private":
        return True

    if not bot_member:
        bot_member = chat.get_member(bot_id)

    return bot_member.status in ("administrator", "creator")

def user_admin(func):
    @wraps(func)
    def is_admin(update: Update, context: CallbackContext, *args, **kwargs):
        if not update.effective_chat or not update.effective_user:
            return
        if is_user_admin(update.effective_chat, update.effective_user.id):
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text("Only admins can use this command!")

    return is_admin

def user_not_admin(func):
    @wraps(func)
    def is_not_admin(update: Update, context: CallbackContext, *args, **kwargs):
        user = update.effective_user
        chat = update.effective_chat

        if user and not is_user_admin(chat, user.id):
            return func(update, context, *args, **kwargs)
        elif not user:
            pass

    return is_not_admin

def bot_admin(func):
    @wraps(func)
    def is_admin(update: Update, context: CallbackContext, *args, **kwargs):
        if not update.effective_chat:
            return
        if is_bot_admin(update.effective_chat, context.bot.id):
            return func(update, context, *args, **kwargs)
        else:
            update.effective_message.reply_text("I need to be an admin to function properly!")

    return is_admin

def user_can_delete(func):
    @wraps(func)
    def delete_rights(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_delete = "I can't delete messages here!\nMake sure I'm admin and can delete other user's messages."
            if chat.get_member(bot.id).can_delete_messages:
                return func(update, context, *args, **kwargs)
            else:
                update.effective_message.reply_text(cant_delete)

    return delete_rights

def user_can_ban(func):
    @wraps(func)
    def ban_rights(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_ban = "I can't restrict people here!\nMake sure I'm admin and can restrict users."
            if chat.get_member(bot.id).can_restrict_members:
                return func(update, context, *args, **kwargs)
            else:
                update.effective_message.reply_text(cant_ban)

    return ban_rights

def user_can_pin(func):
    @wraps(func)
    def pin_rights(update: Update, context: CallbackContext, *args, **kwargs):
        bot = context.bot
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_pin = "I can't pin messages here!\nMake sure I'm admin and can pin messages."
            if chat.get_member(bot.id).can_pin_messages:
                return func(update, context, *args, **kwargs)
            else:
                update.effective_message.reply_text(cant_pin)

    return pin_rights

def can_delete(chat: Chat, bot_id: int) -> bool:
    return chat.get_member(bot_id).can_delete_messages

def can_restrict(chat: Chat, bot_id: int) -> bool:
    return chat.get_member(bot_id).can_restrict_members

def can_pin(chat: Chat, bot_id: int) -> bool:
    return chat.get_member(bot_id).can_pin_messages

def owner_only(func):
    @wraps(func)
    def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        logger.info(f"Owner check - User ID: {user_id}, Owner ID: {Config.OWNER_ID}, Match: {user_id == Config.OWNER_ID}")
        
        # Also check if user is in DRAGONS list
        is_sudo = user_id in Config.DRAGONS
        logger.info(f"Sudo check - In DRAGONS: {is_sudo}")
        
        if user_id != Config.OWNER_ID and not is_sudo:
            update.effective_message.reply_text(
                "This command is restricted to bot owner only!"
            )
            logger.warning(f"Unauthorized /ai attempt by user {user_id}")
            return
        return func(update, context, *args, **kwargs)
    return wrapped

def can_promote(func):
    @wraps(func)
    def promote_rights(update: Update, context: CallbackContext, *args, **kwargs):
        bot_member = update.effective_chat.get_member(context.bot.id)

        if not bot_member.can_promote_members:
            update.effective_message.reply_text("I don't have the right to promote/demote people here!")
            return

        return func(update, context, *args, **kwargs)

    return promote_rights 
