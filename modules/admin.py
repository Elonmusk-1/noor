from telegram import Update, Chat, User, ParseMode
from telegram.ext import CallbackContext
from telegram.error import BadRequest
from telegram.utils.helpers import mention_html

from modules.helper_funcs.chat_status import bot_admin, user_admin, can_promote
from modules.helper_funcs.extraction import extract_user
from modules.helper_funcs.admin_rights import user_can_changeinfo

@bot_admin
@user_admin
@can_promote
async def promote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = chat.get_member(user.id)

    if not (promoter.can_promote_members or promoter.status == "creator"):
        message.reply_text("You don't have the necessary rights to do that!")
        return

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status == 'administrator' or user_member.status == 'creator':
        message.reply_text("How am I meant to promote someone that's already an admin?")
        return

    if user_id == bot.id:
        message.reply_text("I can't promote myself! Get an admin to do it for me.")
        return

    # Set same permissions as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            can_pin_messages=bot_member.can_pin_messages,
        )

        message.reply_text(
            f"Successfully promoted {mention_html(user_member.user.id, user_member.user.first_name)}!",
            parse_mode=ParseMode.HTML,
        )

    except BadRequest as err:
        message.reply_text(
            f"Could not promote. Error: {err.message}"
        ) 
