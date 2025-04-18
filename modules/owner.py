from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler
from telegram.error import BadRequest

from vars import Vars
from .helper_funcs.chat_status import owner_only

@owner_only
def send(update: Update, context: CallbackContext) -> None:
    """Send a message as the bot. Owner only command."""
    chat = update.effective_chat
    message = update.effective_message
    args = message.text.split(None, 1)
    
    # Check if there's a message to send
    if len(args) < 2:
        message.reply_text("Please provide a message to send!")
        return
        
    text = args[1]
    
    try:
        # If replying to a message, send to that chat
        if message.reply_to_message:
            target_chat = message.reply_to_message.forward_from_chat.id if message.reply_to_message.forward_from_chat else chat.id
        else:
            target_chat = chat.id
            
        context.bot.send_message(
            chat_id=target_chat,
            text=text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # If sending to a different chat, confirm to the owner
        if target_chat != chat.id:
            message.reply_text("Message sent!")
            
    except BadRequest as err:
        message.reply_text(f"Failed to send message: {str(err)}") 