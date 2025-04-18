import html
from typing import Optional

from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.error import BadRequest

from .helper_funcs.chat_status import user_admin, bot_admin
from .helper_funcs.extraction import extract_user
from .sql import warns_sql as sql

@user_admin
@bot_admin
def warn_user(update: Update, context: CallbackContext) -> str:
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    warner = update.effective_user

    user_id = extract_user(message, args)
    if not user_id:
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest:
        return

    if member.status in ('administrator', 'creator'):
        message.reply_text("I can't warn admins!")
        return

    if user_id == context.bot.id:
        message.reply_text("I'm not going to warn myself!")
        return

    # Get warn reason
    if len(args) > 1:
        reason = " ".join(args[1:])
    else:
        reason = None

    # Add warn
    num = sql.warn_user(user_id, chat.id, reason)
    if num >= 3:  # Max warns
        try:
            chat.kick_member(user_id)
            message.reply_text("That's 3 warns, {} has been banned!".format(
                mention_html(member.user.id, member.user.first_name)), 
                parse_mode=ParseMode.HTML)
            return "<b>{}:</b>" \
                   "\n#BANNED" \
                   "\n<b>User:</b> {}" \
                   "\n<b>Reason:</b> Max warnings exceeded".format(
                       html.escape(chat.title),
                       mention_html(member.user.id, member.user.first_name))

        except BadRequest:
            message.reply_text("I can't ban people here! Make sure I'm admin!")
            return

    else:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("Remove warn ⚠️", 
                callback_data="rm_warn({})".format(user_id))
        ]])

        reply = "{} has been warned! They have {}/{} warnings.".format(
            mention_html(member.user.id, member.user.first_name), num, 3)
        if reason:
            reply += "\nReason: {}".format(html.escape(reason))

        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return "<b>{}:</b>" \
               "\n#WARN" \
               "\n<b>User:</b> {}" \
               "\n<b>Count:</b> {}/3".format(html.escape(chat.title),
                                           mention_html(member.user.id, member.user.first_name), num) 