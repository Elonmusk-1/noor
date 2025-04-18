from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler
from telegram.error import BadRequest
from telegram.utils.helpers import mention_html

def info(update: Update, context: CallbackContext):
    args = context.args
    msg = update.effective_message
    user_id = extract_user(msg, args)
    chat = update.effective_chat

    if user_id:
        user = context.bot.get_chat(user_id)
    else:
        user = msg.from_user

    text = (
        f"<b>User Information:</b>\n"
        f"ID: <code>{user.id}</code>\n"
        f"First Name: {html.escape(user.first_name)}"
    )

    if user.last_name:
        text += f"\nLast Name: {html.escape(user.last_name)}"

    if user.username:
        text += f"\nUsername: @{html.escape(user.username)}"

    text += f"\nPermanent user link: {mention_html(user.id, 'link')}"

    try:
        member = chat.get_member(user.id)
        if member.status == 'administrator':
            text += "\n\nThis user is an <b>Admin</b>"
        elif member.status == 'creator':
            text += "\n\nThis user is the group <b>Creator</b>"
    except BadRequest:
        pass

    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML) 