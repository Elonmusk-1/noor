from telegram import Update, ParseMode, Chat
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters
from telegram.error import BadRequest

import google.generativeai as genai
from config import Config
from .sql import group_ai_sql as sql
import logging

logger = logging.getLogger(__name__)

# Add error handling for API key configuration
try:
    genai.configure(api_key=Config.GEMINI_API_KEY)
    if not Config.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not configured")
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {str(e)}")

DEFAULT_PROMPT = """You are a helpful assistant in a Telegram group chat. 
Keep responses concise and friendly. If you don't know something, say so.
Avoid harmful or inappropriate content."""

def get_ai_response(prompt: str, message: str) -> str:
    """Get response from Google Gemini API"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        full_prompt = f"{prompt}\n\nUser: {message}"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error in get_ai_response: {str(e)}")
        return f"Error getting AI response: {str(e)}"

def is_owner(update: Update) -> bool:
    """Check if user is the bot owner or admin"""
    user_id = update.effective_user.id
    return user_id == Config.OWNER_ID or user_id in Config.DRAGONS

def group_ai_toggle(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    args = context.args

    # Debug logging
    logger.info(f"=== Group AI Toggle Debug ===")
    logger.info(f"User ID: {user.id}")
    logger.info(f"Chat ID: {chat.id}")
    logger.info(f"Chat Type: {chat.type}")
    logger.info(f"Args: {args}")
    logger.info(f"Is Owner: {is_owner(update)}")

    # Check if it's a group
    if chat.type not in ["group", "supergroup"]:
        message.reply_text(
            "❌ This command only works in groups!",
            parse_mode=ParseMode.HTML
        )
        return

    # Owner check
    if not is_owner(update):
        message.reply_text(
            "❌ Only bot owner can enable/disable AI chat!",
            parse_mode=ParseMode.HTML
        )
        return

    # Check bot permissions
    try:
        bot_member = chat.get_member(context.bot.id)
        if not bot_member.can_send_messages:
            message.reply_text(
                "❌ I need permission to send messages in this group!",
                parse_mode=ParseMode.HTML
            )
            return
    except Exception as e:
        logger.error(f"Error checking bot permissions: {e}")
        message.reply_text(
            "❌ Error checking bot permissions. Make sure I'm an admin!",
            parse_mode=ParseMode.HTML
        )
        return

    try:
        if not args:
            enabled, _ = sql.get_group_ai_settings(chat.id)
            status = "✅ Enabled" if enabled else "❌ Disabled"
            message.reply_text(
                f"Group AI Chat is currently: {status}\n"
                "Use /gai on/off to toggle",
                parse_mode=ParseMode.HTML
            )
            return

        if args[0].lower() in ('on', 'yes', 'true'):
            success = sql.toggle_group_ai(chat.id, True)
            if success:
                message.reply_text(
                    "✅ AI chat enabled in this group!\n"
                    "• Use /gchat to talk with the AI\n"
                    "• Reply to my messages to continue conversations",
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"AI enabled in group {chat.id} by {user.id}")
            else:
                raise Exception("Failed to enable group AI")
        elif args[0].lower() in ('off', 'no', 'false'):
            success = sql.toggle_group_ai(chat.id, False)
            if success:
                message.reply_text(
                    "❌ AI chat disabled in this group!",
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"AI disabled in group {chat.id} by {user.id}")
            else:
                raise Exception("Failed to disable group AI")
        else:
            message.reply_text(
                "❌ Invalid option! Use 'on/off' or 'yes/no'",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Error in group_ai_toggle: {str(e)}")
        message.reply_text(
            "❌ An error occurred while updating group AI settings.",
            parse_mode=ParseMode.HTML
        )

def group_chat_with_ai(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message

    # Check if it's a group
    if chat.type not in ["group", "supergroup"]:
        return
    
    # Check bot permissions
    try:
        bot_member = chat.get_member(context.bot.id)
        if not bot_member.can_send_messages:
            return
    except:
        return

    # Check if AI is enabled for this group
    enabled, custom_prompt = sql.get_group_ai_settings(chat.id)
    if not enabled:
        if message.text and message.text.startswith('/gchat'):
            message.reply_text(
                "❌ AI chat is disabled in this group.\n"
                "Ask the bot owner to enable it with /gai on",
                parse_mode=ParseMode.HTML
            )
        return

    # Get the message text
    if message.reply_to_message:
        if message.reply_to_message.from_user.id != context.bot.id:
            return
        text = message.text
    else:
        if not message.text or not message.text.startswith('/gchat'):
            return
        text = message.text.replace('/gchat', '', 1).strip()

    if not text:
        message.reply_text(
            "❓ Please provide a message!",
            parse_mode=ParseMode.HTML
        )
        return

    # Get AI response
    prompt = custom_prompt or DEFAULT_PROMPT
    response = get_ai_response(prompt, text)

    try:
        message.reply_text(
            response, 
            reply_to_message_id=message.message_id,
            parse_mode=ParseMode.HTML
        )
    except BadRequest as e:
        if 'Message is too long' in str(e):
            for i in range(0, len(response), 4096):
                message.reply_text(
                    response[i:i+4096],
                    reply_to_message_id=message.message_id,
                    parse_mode=ParseMode.HTML
                )

def __help__(update: Update) -> str:
    return """
*Group AI Chat Commands:*
• `/gai` [on/off]: Enable/disable AI chat in groups (Bot owner only)
• `/gchat` <message>: Chat with the AI in groups
• Reply to my messages to continue the conversation

Note: AI chat must be enabled in each group separately.
"""

def __mod_name__() -> str:
    return "Group AI Chat"

__handlers__ = [
    CommandHandler(["groupai", "gai"], group_ai_toggle, run_async=True),
    CommandHandler("gchat", group_chat_with_ai, run_async=True),
    MessageHandler(
        Filters.text & ~Filters.command & Filters.reply & Filters.chat_type.groups,
        group_chat_with_ai,
        run_async=True
    )
] 

