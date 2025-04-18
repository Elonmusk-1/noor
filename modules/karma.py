from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters
from telegram.error import BadRequest
import logging
from datetime import datetime, timedelta
import re

from . import sql

# Set up logging with more detail
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

_karma_timeout = {}  # Dict to store last karma time for each user

# Define the karma regex pattern
KARMA_PATTERN = r'(?i)^(\+|👍|\-|👎|\+1|\-1|thanks|thank you|ty)$'

def test_karma_pattern():
    """Test the karma regex pattern"""
    test_strings = ["+", "👍", "+1", "thanks", "thank you", "ty", "-", "👎", "-1"]
    logger.info("Testing karma regex pattern:")
    for s in test_strings:
        matches = bool(re.match(KARMA_PATTERN, s, re.IGNORECASE))
        logger.info(f"Testing '{s}': {matches}")

def karma_handler(update: Update, context: CallbackContext) -> None:
    try:
        message = update.effective_message
        chat = update.effective_chat
        user = message.from_user
        
        logger.debug(f"=== Karma Handler Debug ===")
        logger.debug(f"Message text: {message.text}")
        logger.debug(f"Chat ID: {chat.id}")
        logger.debug(f"User ID: {user.id}")
        logger.debug(f"Chat type: {chat.type}")
        logger.debug(f"Is reply: {bool(message.reply_to_message)}")
        
        # Test if message matches our pattern
        matches = re.match(KARMA_PATTERN, message.text, re.IGNORECASE)
        logger.debug(f"Matches karma pattern: {bool(matches)}")
        
        # Rate limiting
        timeout_key = f"{chat.id}:{user.id}"
        if timeout_key in _karma_timeout:
            remaining_time = _karma_timeout[timeout_key] - datetime.now()
            if remaining_time.total_seconds() > 0:
                logger.debug(f"Rate limited. Remaining time: {remaining_time.total_seconds()}s")
                message.reply_text(f"Please wait {int(remaining_time.total_seconds())} seconds before giving karma again!")
                return
                
        # Only work in groups
        if chat.type not in ["group", "supergroup"]:
            logger.debug(f"Wrong chat type: {chat.type}")
            message.reply_text("This command only works in groups!")
            return
            
        if not message.reply_to_message:
            logger.debug("No reply to message")
            message.reply_text("Reply to a message to give karma!")
            return
            
        target_user = message.reply_to_message.from_user
        if not target_user:
            logger.debug("Could not determine target user")
            message.reply_text("Could not determine user from the replied message.")
            return
            
        logger.debug(f"Target user ID: {target_user.id}")
        
        # Don't allow karma manipulation on oneself
        if target_user.id == user.id:
            logger.debug("User tried to give karma to themselves")
            message.reply_text("You can't give karma to yourself! 😉")
            return
            
        # Don't allow karma for bots
        if target_user.is_bot:
            logger.debug("Target user is a bot")
            message.reply_text("Bots don't need karma! 🤖")
            return
            
        karma_amount = 0
        text = message.text.lower()
        logger.debug(f"Karma text: {text}")
        
        if text in ["+", "👍", "+1", "thanks", "thank you", "ty"]:
            karma_amount = 1
        elif text in ["-", "👎", "-1"]:
            karma_amount = -1
            
        if karma_amount != 0:
            _karma_timeout[timeout_key] = datetime.now() + timedelta(seconds=30)  # 30 second cooldown
            try:
                new_karma = sql.update_karma(chat.id, target_user.id, karma_amount)
                message.reply_text(
                    f"{'Increased' if karma_amount > 0 else 'Decreased'} karma for {target_user.mention_html()}! "
                    f"New karma: {new_karma} {'⭐' if karma_amount > 0 else '💫'}",
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"Updated karma for user {target_user.id} in chat {chat.id} by {karma_amount}")
            except Exception as e:
                logger.error(f"Error updating karma: {str(e)}")
                message.reply_text("Failed to update karma. Please try again later.")
                
    except Exception as e:
        logger.error(f"Error in karma_handler: {str(e)}")
        message.reply_text("An error occurred while processing karma. Please try again later.")

def check_karma(update: Update, context: CallbackContext) -> None:
    """Check karma for a user"""
    try:
        message = update.effective_message
        chat = update.effective_chat
        
        if not chat or not message:
            return
            
        # Get target user (either replied-to user or command sender)
        if message.reply_to_message:
            user = message.reply_to_message.from_user
        else:
            user = message.from_user
            
        if not user:
            return
            
        # Get karma count
        karma = sql.get_karma(chat.id, user.id)
        
        message.reply_text(
            f"{user.mention_html()}'s karma is: {karma} ⭐",
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.error(f"Error in check_karma: {str(e)}")
        message.reply_text("An error occurred while checking karma.")

def karma_leaderboard(update: Update, context: CallbackContext) -> None:
    """Show karma leaderboard for the chat"""
    try:
        message = update.effective_message
        chat = update.effective_chat
        
        if not chat or not message:
            return
            
        # Get top karma users
        top_users = sql.get_karma_leaderboard(chat.id)
        if not top_users:
            message.reply_text("No karma records found in this chat!")
            return
            
        # Format leaderboard message
        leaderboard = f"🏆 Karma Leaderboard for {chat.title}:\n\n"
        
        for i, (user_id, karma_count) in enumerate(top_users, 1):
            try:
                user = context.bot.get_chat_member(chat.id, user_id).user
                user_name = user.mention_html() if user else f"User {user_id}"
            except BadRequest:
                user_name = f"User {user_id}"
                
            trophy = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "✨"
            leaderboard += f"{i}. {trophy} {user_name}: {karma_count} points\n"
            
        message.reply_text(leaderboard, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Error in karma_leaderboard: {str(e)}")
        message.reply_text("An error occurred while getting the leaderboard.")

def __mod_name__() -> str:
    return "Karma"

def __help__(update: Update) -> str:
    return """
*Karma System Commands:*
• Reply to a message with +, 👍, or +1 to give karma
• Reply with -, 👎, or -1 to reduce karma
• /karma: Check your karma or reply to check someone else's karma
• /karmatop: Show karma leaderboard for this chat

Note: You cannot give karma to yourself!
"""

# Define karma filter
karma_filter = (
    Filters.regex(KARMA_PATTERN) & 
    Filters.reply & 
    Filters.chat_type.groups
)

__handlers__ = [
    (
        MessageHandler(
            karma_filter,
            karma_handler,
            run_async=True
        ),
        1  # Group priority - lower number means higher priority
    ),
    CommandHandler(
        ["karma", "k"],
        check_karma,
        filters=Filters.chat_type.groups,
        run_async=True
    ),
    CommandHandler(
        ["karmatop", "ktop"],
        karma_leaderboard,
        filters=Filters.chat_type.groups,
        run_async=True
    )
]

logger.info("Karma module loaded. Handlers registered.")
logger.info(f"Registering karma handlers: {__handlers__}")
for handler in __handlers__:
    if isinstance(handler, MessageHandler):
        logger.info(f"Karma MessageHandler filters: {handler.filters}")
        # Test the regex pattern
        test_karma_pattern()
    elif isinstance(handler, CommandHandler):
        logger.info(f"Karma CommandHandler: {handler.command}")

def init_module():
    """Initialize the karma module"""
    logger.info("Initializing karma module...")
    
    # Test the karma pattern
    test_karma_pattern()
    
    # Log the filter configuration
    logger.info("Karma filter configuration:")
    logger.info(f"Pattern: {KARMA_PATTERN}")
    logger.info(f"Complete filter: {karma_filter}")
    
    # Log handlers
    for handler in __handlers__:
        if isinstance(handler, MessageHandler):
            logger.info(f"Registered MessageHandler with filters: {handler.filters}")
            # Test some sample messages
            test_messages = ["+", "👍", "+1", "thanks", "thank you", "ty", "-", "👎", "-1"]
            for msg in test_messages:
                logger.info(f"Would match '{msg}': {bool(re.match(KARMA_PATTERN, msg, re.IGNORECASE))}")
        elif isinstance(handler, CommandHandler):
            logger.info(f"Registered CommandHandler: {handler.command}")
    
    return True

init_module() 
