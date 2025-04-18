from telegram import Update, ChatPermissions
from telegram.ext import CallbackContext, MessageHandler, Filters
from telegram.error import BadRequest

from .helper_funcs.chat_status import bot_admin, user_admin
from .sql import antiflood_sql as sql

FLOOD_GROUP = 3

def check_flood(update: Update, context: CallbackContext) -> str:
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message

    if not user:  # ignore channels
        return ""

    # ignore admins
    if user.id in ADMIN_LIST:
        sql.update_flood(chat.id, None)
        return ""

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        chat.kick_member(user.id)
        msg.reply_text(f"*bans user*\nReason: Flooding chat")

        return (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#BANNED\n"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
            f"Reason: Flooding chat"
        )

    except BadRequest:
        msg.reply_text("I can't kick people here, give me permissions first!")
        sql.set_flood(chat.id, 0)
        return ""

@user_admin
def set_flood(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    args = context.args

    if len(args) >= 1:
        val = args[0].lower()
        if val in ["off", "no", "0"]:
            sql.set_flood(chat.id, 0)
            update.effective_message.reply_text("Antiflood has been disabled.")
        elif val.isdigit():
            amount = int(val)
            sql.set_flood(chat.id, amount)
            update.effective_message.reply_text(f"Antiflood settings updated to {amount} messages.") 