from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters
from telegram.error import BadRequest

from .helper_funcs.chat_status import user_admin
from .sql import autofilter_sql as sql

@user_admin
def add_filter(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    
    if not args:
        message.reply_text(
            "Please specify what to filter!\n"
            "Available options: url, sticker, forward, image"
        )
        return
        
    filter_type = args[0].lower()
    if filter_type not in ["url", "sticker", "forward", "image"]:
        message.reply_text("Invalid filter type!")
        return
        
    sql.toggle_filter(chat.id, filter_type, True)
    message.reply_text(f"Added auto-filter for {filter_type}s!")

@user_admin
def remove_filter(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    
    if not args:
        message.reply_text("Please specify which filter to remove!")
        return
        
    filter_type = args[0].lower()
    if filter_type not in ["url", "sticker", "forward", "image"]:
        message.reply_text("Invalid filter type!")
        return
        
    sql.toggle_filter(chat.id, filter_type, False)
    message.reply_text(f"Removed auto-filter for {filter_type}s!")

def list_filters(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    
    filters = sql.get_filters(chat.id)
    if not filters:
        message.reply_text("No auto-filters active in this chat!")
        return
        
    text = "*Active Auto-Filters:*\n"
    for filter_type, enabled in filters.items():
        text += f"• {filter_type}: {'✅' if enabled else '❌'}\n"
        
    message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

def handle_filters(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    
    filters = sql.get_filters(chat.id)
    if not filters:
        return
        
    should_delete = False
    
    if filters.get("urls") and message.entities:
        for entity in message.entities:
            if entity.type in ["url", "text_link"]:
                should_delete = True
                break
                
    if filters.get("stickers") and message.sticker:
        should_delete = True
        
    if filters.get("forwards") and message.forward_from:
        should_delete = True
        
    if filters.get("images") and message.photo:
        should_delete = True
        
    if should_delete:
        try:
            message.delete()
        except BadRequest:
            pass 