from telegram import Update, ChatPermissions
from telegram.ext import CallbackContext, CommandHandler
from telegram.error import BadRequest

from .helper_funcs.chat_status import bot_admin, user_admin
from .helper_funcs.extraction import extract_user

@bot_admin
@user_admin
def mute(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id = extract_user(message, args)
    if not user_id:
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest:
        return

    if member.status in ('administrator', 'creator'):
        message.reply_text("I can't mute admins!")
        return

    if user_id == bot.id:
        message.reply_text("I'm not going to MUTE myself!")
        return

    try:
        bot.restrict_chat_member(
            chat.id,
            user_id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
            )
        )
        message.reply_text(f"Muted user {member.user.first_name}!")
        return f"<b>{html.escape(chat.title)}:</b>\n#MUTE\n<b>Admin:</b> {mention_html(user.id, user.first_name)}\n<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"

    except BadRequest as excp:
        message.reply_text(f"Error: {excp.message}")
        return 