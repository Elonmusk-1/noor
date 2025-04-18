from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters
from telegram.error import BadRequest
import re

from .helper_funcs.chat_status import user_admin, user_not_admin
from .sql import blacklist_sql as sql

@user_admin
def add_blacklist(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message
    chat = update.effective_chat
    words = msg.text.split(None, 1)
    
    if len(words) > 1:
        text = words[1]
        to_blacklist = list({trigger.strip() for trigger in text.split("\n") if trigger.strip()})
        
        for trigger in to_blacklist:
            sql.add_to_blacklist(chat.id, trigger.lower())
        
        msg.reply_text(
            f"Added {len(to_blacklist)} triggers to the blacklist.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        msg.reply_text(
            "Tell me which words you would like to add to the blacklist."
        )

@user_admin
def remove_blacklist(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message
    chat = update.effective_chat
    words = msg.text.split(None, 1)
    
    if len(words) > 1:
        text = words[1]
        to_unblacklist = list({trigger.strip() for trigger in text.split("\n") if trigger.strip()})
        successful = 0
        
        for trigger in to_unblacklist:
            success = sql.rm_from_blacklist(chat.id, trigger.lower())
            if success:
                successful += 1
        
        msg.reply_text(
            f"Removed {successful} triggers from the blacklist.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        msg.reply_text(
            "Tell me which words you would like to remove from the blacklist."
        )

def list_blacklist(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    
    all_blacklisted = sql.get_chat_blacklist(chat.id)
    
    if not all_blacklisted:
        update.effective_message.reply_text(
            "No blacklisted words in this chat!"
        )
        return
    
    msg = "Current blacklisted words:\n"
    for trigger in all_blacklisted:
        msg += f"- `{trigger}`\n"
    
    update.effective_message.reply_text(
        msg,
        parse_mode=ParseMode.MARKDOWN
    )

@user_not_admin
def del_blacklist(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    
    to_match = message.text or message.caption
    if not to_match:
        return
    
    chat_filters = sql.get_chat_blacklist(chat.id)
    for trigger in chat_filters:
        pattern = r"( |^|[^\w])" + trigger + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            try:
                message.delete()
            except BadRequest as excp:
                if excp.message != "Message to delete not found":
                    logger.error("Error while deleting blacklist message.")
            break

def __help__(update: Update) -> str:
    return """
*Blacklist Commands:*
• `/blacklist`: List all blacklisted words
• `/addblacklist <words>`: Add words to the blacklist
• `/rmblacklist <words>`: Remove words from the blacklist
"""

def __mod_name__() -> str:
    return "Blacklist"

__handlers__ = [
    CommandHandler(["blacklist", "bl"], list_blacklist),
    CommandHandler("addblacklist", add_blacklist),
    CommandHandler("rmblacklist", remove_blacklist),
    MessageHandler(
        (Filters.text | Filters.command | Filters.sticker | Filters.photo) & 
        Filters.chat_type.groups,
        del_blacklist,
    ),
] 

