from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram.error import BadRequest
from datetime import datetime

from .helper_funcs.chat_status import user_admin
from .sql import logging_sql as sql

def format_log_message(event_type: str, chat_title: str, user=None, **kwargs) -> str:
    """Format log messages based on event type"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    base_text = f"**{event_type}** in *{chat_title}*\n"
    base_text += f"Time: `{timestamp}`\n"
    
    if user:
        base_text += f"User: {user.mention_html()} (`{user.id}`)\n"
    
    # Add event-specific details
    if "old_message" in kwargs:
        base_text += f"Old message: `{kwargs['old_message']}`\n"
    if "new_message" in kwargs:
        base_text += f"New message: `{kwargs['new_message']}`\n"
    if "reason" in kwargs:
        base_text += f"Reason: `{kwargs['reason']}`\n"
    if "duration" in kwargs:
        base_text += f"Duration: `{kwargs['duration']}`\n"
        
    return base_text

@user_admin
def set_log(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    
    if not args:
        log_channel = sql.get_log_channel(chat.id)
        if log_channel:
            message.reply_text(
                f"Current log channel: {log_channel}\n"
                "Use /setlog with channel ID to change it."
            )
        else:
            message.reply_text("No log channel set!")
        return
        
    try:
        channel_id = str(args[0])
        # Try to send a message to verify bot has access
        test_msg = context.bot.send_message(
            channel_id,
            "Setting up logging channel..."
        )
        test_msg.delete()
        
        sql.set_log_channel(chat.id, channel_id)
        message.reply_text(f"Successfully set log channel to: {channel_id}")
        
    except BadRequest as e:
        message.reply_text(f"Failed to set log channel: {str(e)}")

@user_admin
def unset_log(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    
    sql.unset_log_channel(chat.id)
    message.reply_text("Successfully disabled logging!")

@user_admin
def log_settings(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    
    settings = sql.get_log_settings(chat.id)
    if not settings:
        message.reply_text("No logging settings configured!")
        return
        
    keyboard = []
    for log_type, enabled in settings.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{log_type.title()}: {'✅' if enabled else '❌'}",
                callback_data=f"log_{log_type}_{not enabled}"
            )
        ])
        
    message.reply_text(
        "📝 *Logging Settings*\nClick to toggle each type:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

def log_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    chat = update.effective_chat
    
    log_type, enabled = query.data.split('_')[1:]
    enabled = enabled.lower() == 'true'
    
    sql.toggle_log_type(chat.id, log_type, enabled)
    
    # Update keyboard
    settings = sql.get_log_settings(chat.id)
    keyboard = []
    for type_, is_enabled in settings.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{type_.title()}: {'✅' if is_enabled else '❌'}",
                callback_data=f"log_{type_}_{not is_enabled}"
            )
        ])
        
    query.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    query.answer(f"{log_type.title()} logging {'enabled' if enabled else 'disabled'}")

def log_action(update: Update, context: CallbackContext) -> None:
    """Log various chat actions"""
    chat = update.effective_chat
    message = update.effective_message
    
    log_channel = sql.get_log_channel(chat.id)
    if not log_channel:
        return
        
    settings = sql.get_log_settings(chat.id)
    if not settings:
        return
        
    try:
        # Log message edits
        if message.edit_date and settings.get('edit'):
            log_text = format_log_message(
                "MESSAGE EDITED",
                chat.title,
                message.from_user,
                old_message=message.text,
                new_message=message.edit_text
            )
            context.bot.send_message(
                log_channel,
                log_text,
                parse_mode=ParseMode.HTML
            )
            
        # Log message deletions
        elif message.delete_date and settings.get('delete'):
            log_text = format_log_message(
                "MESSAGE DELETED",
                chat.title,
                message.from_user,
                old_message=message.text
            )
            context.bot.send_message(
                log_channel,
                log_text,
                parse_mode=ParseMode.HTML
            )
            
        # Log member updates
        elif message.new_chat_members and settings.get('member'):
            for member in message.new_chat_members:
                log_text = format_log_message(
                    "MEMBER JOINED",
                    chat.title,
                    member
                )
                context.bot.send_message(
                    log_channel,
                    log_text,
                    parse_mode=ParseMode.HTML
                )
                
        # Log member leaves
        elif message.left_chat_member and settings.get('member'):
            log_text = format_log_message(
                "MEMBER LEFT",
                chat.title,
                message.left_chat_member
            )
            context.bot.send_message(
                log_channel,
                log_text,
                parse_mode=ParseMode.HTML
            )
            
    except BadRequest:
        pass  # Channel not found or bot was removed 

__handlers__ = [
    CommandHandler("setlog", set_log, filters=Filters.chat_type.groups),
    CommandHandler("unsetlog", unset_log, filters=Filters.chat_type.groups),
    CommandHandler("logsettings", log_settings, filters=Filters.chat_type.groups),
    CallbackQueryHandler(log_button, pattern=r"^log_"),
    MessageHandler(
        Filters.chat_type.groups & (Filters.text | Filters.sticker | Filters.photo),
        log_action,
        run_async=True
    )
] 
