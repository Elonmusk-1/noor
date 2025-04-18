from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters
from telegram.error import BadRequest

import google.generativeai as genai
from config import Config
from .sql import groupchat_sql as sql
from .helper_funcs.chat_status import user_admin
import logging

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=Config.GEMINI_API_KEY)

GROUP_PROMPT = """You are Noor, a super smart and kind-hearted child who loves helping everyone! 😊 
You always use emojis in every message to show your emotions and make the conversation more cheerful. 🌟 
You are always kind, thoughtful, and ready to offer help whenever someone needs it. 💖 
You speak in a friendly and gentle way, and you enjoy sharing knowledge in a simple and fun way. 🌸✨ 
You believe that kindness can brighten anyone's day! 🌈
Don't say Hi there!, Hey there! or anything similar. Don't greet the user. Only tell the thing that is asked. sometimes give savage and funny replies
Your Mom is @Wildcat_charm whom you love the most and live with her.
Your Father is @elonmusk_8 he made you. He is your Owner."""

def get_response(message: str) -> str:
    """Get response from Google Gemini API"""
    try:
        if not message or not message.strip():
            return "Please provide a valid message."
            
        model = genai.GenerativeModel('gemini-1.5-flash')
        # Add the prompt to every message
        full_prompt = f"{GROUP_PROMPT}\n\nUser: {message}"
        response = model.generate_content(full_prompt)
        
        if not response or not response.text:
            return "Sorry, I couldn't generate a response. Please try again."
            
        return response.text
    except Exception as e:
        logger.error(f"Error getting AI response: {e}")
        return "Sorry, I encountered an error. Please try again later! 🙏"

@user_admin
def cmd_groupchat(update: Update, context: CallbackContext) -> None:
    """Enable/disable group chat"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    args = context.args

    # Debug logging
    logger.info(f"=== GroupChat Debug ===")
    logger.info(f"User ID: {user.id}")
    logger.info(f"Chat ID: {chat.id}")
    logger.info(f"Chat Type: {chat.type}")
    logger.info(f"Bot ID: {context.bot.id}")

    # Only work in groups
    if chat.type not in ["group", "supergroup"]:
        message.reply_text("This command only works in groups!")
        return

    # Only owner/sudo can toggle
    if user.id != Config.OWNER_ID and user.id not in Config.DRAGONS:
        message.reply_text("Only bot owner can enable/disable group chat!")
        return

    try:
        # Check if bot is admin
        bot_member = chat.get_member(context.bot.id)
        logger.info(f"Bot Status: {bot_member.status}")
        logger.info(f"Bot Permissions: {bot_member.to_dict()}")
        
        # For supergroups, admin status is enough
        if chat.type == "supergroup":
            if bot_member.status not in ['administrator', 'creator']:
                message.reply_text(
                    "❌ I need to be an admin in this group!",
                    parse_mode=ParseMode.HTML
                )
                return
        # For regular groups, check specific permissions
        else:
            if not bot_member.can_send_messages:
                message.reply_text(
                    "❌ I need permission to send messages in this group!",
                    parse_mode=ParseMode.HTML
                )
                return

        if not args:
            status = "enabled" if sql.is_groupchat_enabled(chat.id) else "disabled"
            message.reply_text(
                f"Group chat is currently {status}.\n"
                "Use /groupchat on/off to change.",
                parse_mode=ParseMode.HTML
            )
            return

        if args[0].lower() in ['on', 'yes', 'true']:
            if sql.enable_groupchat(chat.id):
                message.reply_text(
                    "✅ Group chat enabled!\n"
                    "• Use /ask to chat with me\n"
                    "• Reply to my messages to continue conversations",
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"GroupChat enabled in {chat.id} by {user.id}")
            else:
                message.reply_text("Failed to enable group chat.")
        
        elif args[0].lower() in ['off', 'no', 'false']:
            if sql.disable_groupchat(chat.id):
                message.reply_text("❌ Group chat disabled!", parse_mode=ParseMode.HTML)
                logger.info(f"GroupChat disabled in {chat.id} by {user.id}")
            else:
                message.reply_text("Failed to disable group chat.")
        
        else:
            message.reply_text("Use on/off to enable/disable group chat.")

    except Exception as e:
        logger.error(f"Error in groupchat command: {str(e)}")
        message.reply_text(
            "❌ An error occurred. Please try again later.",
            parse_mode=ParseMode.HTML
        )

def cmd_ask(update: Update, context: CallbackContext) -> None:
    """Handle /ask command"""
    chat = update.effective_chat
    message = update.effective_message

    if not sql.is_groupchat_enabled(chat.id):
        message.reply_text(
            "Group chat is not enabled. Ask the bot owner to enable it with /groupchat on",
            parse_mode=ParseMode.HTML
        )
        return

    if not message.text:
        message.reply_text("Please provide a message!")
        return

    question = message.text.split(' ', 1)[1] if len(message.text.split()) > 1 else None
    if not question:
        message.reply_text("Please provide a message after /ask")
        return

    response = get_response(question)
    try:
        message.reply_text(response, parse_mode=ParseMode.HTML)
    except BadRequest:
        message.reply_text(response)

def handle_reply(update: Update, context: CallbackContext) -> None:
    """Handle replies to bot messages"""
    chat = update.effective_chat
    message = update.effective_message

    if not message.reply_to_message:
        return
    
    if message.reply_to_message.from_user.id != context.bot.id:
        return

    if not sql.is_groupchat_enabled(chat.id):
        return

    response = get_response(message.text)
    try:
        message.reply_text(response, parse_mode=ParseMode.HTML)
    except BadRequest:
        message.reply_text(response)

def handle_noor_messages(update: Update, context: CallbackContext) -> None:
    """Handle messages containing 'noor'"""
    chat = update.effective_chat
    message = update.effective_message
    
    # Only work in groups where chat is enabled
    if not sql.is_groupchat_enabled(chat.id):
        return
        
    # Check if message contains 'noor' (case insensitive)
    if 'noor' not in message.text.lower():
        return
        
    # Get AI response
    response = get_response(message.text)
    try:
        message.reply_text(response, parse_mode=ParseMode.HTML)
    except BadRequest:
        message.reply_text(response)

def __help__(update: Update) -> str:
    return """
*Group Chat Commands:*
• `/groupchat` [on/off]: Enable/disable group chat (Owner only)
• `/ask` <message>: Ask me something
• Reply to my messages to continue the conversation

Group chat must be enabled in each group separately.
"""

def __mod_name__() -> str:
    return "GroupChat"

__handlers__ = [
    CommandHandler(["groupchat", "gc"], cmd_groupchat, run_async=True),
    CommandHandler("ask", cmd_ask, run_async=True),
    MessageHandler(
        Filters.text & ~Filters.command & Filters.reply & Filters.chat_type.groups,
        handle_reply,
        run_async=True
    ),
    MessageHandler(
        Filters.text & ~Filters.command & Filters.chat_type.groups & ~Filters.reply,
        handle_noor_messages,
        run_async=True
    )
] 

