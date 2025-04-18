from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CommandHandler, Filters
from telegram.error import BadRequest

from .helper_funcs.chat_status import user_admin
from .sql import rules_sql as sql

def get_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    rules = sql.get_rules(chat_id)
    
    if rules:
        update.effective_message.reply_text(
            f"The rules for *{update.effective_chat.title}* are:\n\n{rules}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    text="Rules",
                    url=f"t.me/{context.bot.username}?start=rules_{chat_id}"
                )
            ]])
        )
    else:
        update.effective_message.reply_text(
            "The group admins haven't set any rules for this chat yet. "
            "This probably doesn't mean it's lawless though...!"
        )

@user_admin
def set_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    raw_text = msg.text
    args = raw_text.split(None, 1)

    if len(args) == 2:
        txt = args[1]
        sql.set_rules(chat_id, txt)
        update.effective_message.reply_text("Successfully set rules for this group!")
    else:
        update.effective_message.reply_text("You need to give me some rules to set!")

__handlers__ = [
    CommandHandler(["rules", "r"], get_rules, filters=Filters.chat_type.groups),
    CommandHandler("setrules", set_rules, filters=Filters.chat_type.groups)
] 
