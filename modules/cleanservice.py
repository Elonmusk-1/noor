from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters
from telegram.error import BadRequest

from .helper_funcs.chat_status import user_admin, bot_admin
from .sql import cleanservice_sql as sql

@user_admin
def toggle_service_messages(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    args = context.args
    
    if not args:
        service_status, cmd_status = sql.get_clean_settings(chat.id)
        update.effective_message.reply_text(
            f"Clean service settings for this chat:\n"
            f"Service messages: {'Enabled' if service_status else 'Disabled'}\n"
            f"Command messages: {'Enabled' if cmd_status else 'Disabled'}"
        )
        return
        
    if args[0].lower() in ('on', 'yes', 'true'):
        sql.toggle_clean_service(chat.id, True)
        update.effective_message.reply_text("I'll be deleting service messages from now on!")
    elif args[0].lower() in ('off', 'no', 'false'):
        sql.toggle_clean_service(chat.id, False)
        update.effective_message.reply_text("I'll stop deleting service messages!")
    else:
        update.effective_message.reply_text("Invalid option! Use 'on/off' or 'yes/no'")

@user_admin
def toggle_command_cleanup(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    args = context.args
    
    if not args:
        _, cmd_status = sql.get_clean_settings(chat.id)
        update.effective_message.reply_text(
            f"Command cleanup is currently: {'Enabled' if cmd_status else 'Disabled'}"
        )
        return
        
    if args[0].lower() in ('on', 'yes', 'true'):
        sql.toggle_clean_commands(chat.id, True)
        update.effective_message.reply_text("I'll be deleting command messages from now on!")
    elif args[0].lower() in ('off', 'no', 'false'):
        sql.toggle_clean_commands(chat.id, False)
        update.effective_message.reply_text("I'll stop deleting command messages!")
    else:
        update.effective_message.reply_text("Invalid option! Use 'on/off' or 'yes/no'")

def cleanup_messages(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    
    if not chat or chat.type == "private":
        return
        
    clean_service, clean_commands = sql.get_clean_settings(chat.id)
    
    # Clean service messages
    if clean_service and message.new_chat_members or message.left_chat_member:
        try:
            message.delete()
        except BadRequest:
            pass
            
    # Clean command messages
    if clean_commands and message.text and message.text.startswith('/'):
        # Wait a bit to allow command to be processed
        context.job_queue.run_once(
            lambda _: delete_message(chat.id, message.message_id, context.bot),
            3
        )

def delete_message(chat_id: int, message_id: int, bot):
    try:
        bot.delete_message(chat_id, message_id)
    except BadRequest:
        pass 