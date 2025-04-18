from functools import wraps
from telegram import Update, ChatMember
from telegram.ext import CallbackContext

def user_can_changeinfo(func):
    @wraps(func)
    def can_changeinfo(update: Update, context: CallbackContext, *args, **kwargs):
        user = update.effective_user
        chat = update.effective_chat
        msg = update.effective_message

        if chat.type == 'private':
            return func(update, context, *args, **kwargs)

        member = chat.get_member(user.id)
        if not member.can_change_info and member.status != "creator":
            msg.reply_text("You don't have the necessary rights to do that!")
            return

        return func(update, context, *args, **kwargs)

    return can_changeinfo 