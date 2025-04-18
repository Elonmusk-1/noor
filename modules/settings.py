from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.error import BadRequest

from .helper_funcs.chat_status import user_admin
from .sql import settings_sql as sql

@user_admin
def settings(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    
    # Build settings keyboard
    keyboard = [
        [
            InlineKeyboardButton("Welcome", callback_data="settings_welcome"),
            InlineKeyboardButton("Antiflood", callback_data="settings_flood")
        ],
        [
            InlineKeyboardButton("Blacklist", callback_data="settings_blacklist"),
            InlineKeyboardButton("Reports", callback_data="settings_report")
        ],
        [
            InlineKeyboardButton("Locks", callback_data="settings_locks"),
            InlineKeyboardButton("Warnings", callback_data="settings_warns")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg.reply_text(
        f"*{chat.title} settings*\n\n"
        "Click on the buttons below to change settings:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

def settings_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    
    if not user_admin(chat, user.id):
        query.answer("You're not an admin!")
        return
        
    setting = query.data.split('_')[1]
    
    if setting == "welcome":
        current = sql.get_welc_pref(chat.id)
        if current:
            query.message.edit_text(
                "Welcome messages are currently *enabled*\n"
                "Click the button to disable",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Disable Welcome", callback_data="disable_welcome")
                ]])
            )
        else:
            query.message.edit_text(
                "Welcome messages are currently *disabled*\n"
                "Click the button to enable",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Enable Welcome", callback_data="enable_welcome")
                ]])
            ) 