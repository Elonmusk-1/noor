from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.error import BadRequest

from .helper_funcs.chat_status import user_admin
from .sql import reports_sql as sql

@user_admin
def report_setting(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    args = context.args
    
    if len(args) >= 1:
        if args[0] in ("yes", "on"):
            sql.set_chat_setting(chat.id, True)
            msg.reply_text("Turned on reporting! Admins will be notified when /report is used.")
            
        elif args[0] in ("no", "off"):
            sql.set_chat_setting(chat.id, False)
            msg.reply_text("Turned off reporting! Admins will no longer be notified on /report.")
    else:
        msg.reply_text(f"Current report setting is: `{sql.chat_should_report(chat.id)}`",
                      parse_mode=ParseMode.MARKDOWN)

def report(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    
    if chat and message.reply_to_message and sql.chat_should_report(chat.id):
        reported_user = message.reply_to_message.from_user
        chat_name = chat.title or chat.first_name
        
        if reported_user.id == context.bot.id:
            message.reply_text("Why would I report myself?")
            return
            
        if user.id == reported_user.id:
            message.reply_text("Why would you report yourself?")
            return
            
        if reported_user.id in ADMIN_LIST:
            message.reply_text("Why would I report an admin?")
            return
            
        if message.text.split(None, 1)[1:]:
            reported_reason = message.text.split(None, 1)[1]
        else:
            reported_reason = ""
            
        msg = (f"<b>⚠️ Report from:</b> {chat.title}\n"
               f"<b>• Report by:</b> {mention_html(user.id, user.first_name)}\n"
               f"<b>• Reported user:</b> {mention_html(reported_user.id, reported_user.first_name)}\n")
               
        if reported_reason:
            msg += f"<b>• Reason:</b> {reported_reason}"
            
        # Notify all admins
        for admin in ADMIN_LIST:
            try:
                context.bot.send_message(admin, msg,
                                      parse_mode=ParseMode.HTML,
                                      reply_markup=InlineKeyboardMarkup([[
                                          InlineKeyboardButton(
                                              "➡ Message",
                                              url=f"https://t.me/{chat.username}/{message.reply_to_message.message_id}"
                                          )
                                      ]]))
            except BadRequest:
                pass
                
        message.reply_text(f"{mention_html(user.id, user.first_name)} reported {mention_html(reported_user.id, reported_user.first_name)} to the admins!",
                          parse_mode=ParseMode.HTML) 