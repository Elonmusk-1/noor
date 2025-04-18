from telegram import Update, ParseMode, Chat
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters
from telegram.error import BadRequest

import google.generativeai as genai
from config import Config
from .sql import group_ai_sql as sql
import logging

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=Config.GEMINI_API_KEY)

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

def is_owner(user_id: int) -> bool:
    """Check if user is the bot owner"""
    return user_id == 2036109591

def toggle_ai_chat(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    args = context.args

    # Debug logging
    logger.info(f"=== AI Toggle Debug ===")
    logger.info(f"User ID: {user.id}")
    logger.info(f"Chat ID: {chat.id}")
    logger.info(f"Chat Type: {chat.type}")
    logger.info(f"Args: {args}")
    logger.info(f"Is Owner: {is_owner(user.id)}")

    # Owner check
    if not is_owner(user.id):
        logger.warning(f"Unauthorized AI toggle attempt by user {user.id} in chat {chat.id}")
        message.reply_text(
            "❌ Only the bot owner can enable/disable AI chat!",
            parse_mode=ParseMode.HTML
        )
        return

    try:
        # Check bot permissions in group
        if chat.type != "private":
            bot_member = chat.get_member(context.bot.id)
            if not bot_member.can_send_messages:
                message.reply_text(
                    "❌ I need permission to send messages in this group!",
                    parse_mode=ParseMode.HTML
                )
                return

        if not args:
            enabled, _ = sql.get_group_ai_settings(chat.id)
            status = "✅ Enabled" if enabled else "❌ Disabled"
            message.reply_text(
                f"AI Chat is currently: {status}\n"
                "Use /ai on/off to toggle",
                parse_mode=ParseMode.HTML
            )
            return

        if args[0].lower() in ('on', 'yes', 'true'):
            success = sql.toggle_group_ai(chat.id, True)
            if success:
                message.reply_text(
                    "✅ AI chat enabled!\n"
                    "• Use /chat to talk with the AI\n"
                    "• Reply to my messages to continue conversations",
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"AI enabled in chat {chat.id} by owner")
            else:
                raise Exception("Failed to enable AI")
        elif args[0].lower() in ('off', 'no', 'false'):
            success = sql.toggle_group_ai(chat.id, False)
            if success:
                message.reply_text(
                    "❌ AI chat disabled!",
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"AI disabled in chat {chat.id} by owner")
            else:
                raise Exception("Failed to disable AI")
        else:
            message.reply_text(
                "❌ Invalid option! Use 'on/off' or 'yes/no'",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Error in toggle_ai_chat: {str(e)}")
        message.reply_text(
            "❌ An error occurred while updating AI settings. Please check logs.",
            parse_mode=ParseMode.HTML
        )

def chat_with_ai(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    
    # Check if AI is enabled
    enabled, custom_prompt = sql.get_group_ai_settings(chat.id)
    if not enabled:
        if chat.type == "private" or message.text.startswith('/chat'):
            message.reply_text(
                "❌ AI chat is disabled. Ask the bot owner to enable it with /ai on",
                parse_mode=ParseMode.HTML
            )
        return

    # Get the message text
    if message.reply_to_message:
        if message.reply_to_message.from_user.id != context.bot.id:
            return
        text = message.text
    else:
        if not message.text.startswith('/chat'):
            return
        text = message.text.replace('/chat', '', 1).strip()

    if not text:
        message.reply_text("Please provide a message!")
        return

    # Get AI response
    prompt = custom_prompt or DEFAULT_PROMPT
    response = get_ai_response(prompt, text)

    try:
        message.reply_text(response, reply_to_message_id=message.message_id)
    except BadRequest as e:
        if 'Message is too long' in str(e):
            for i in range(0, len(response), 4096):
                message.reply_text(
                    response[i:i+4096],
                    reply_to_message_id=message.message_id
                )

def __help__(update: Update) -> str:
    return """
*AI Chat Commands:*
• `/ai` [on/off]: Enable/disable AI chat (Bot owner only)
• `/chat` <message>: Chat with the AI

In groups:
- Only bot owner can enable/disable AI chat
- Anyone can use /chat once enabled
- Reply to my messages to continue the conversation
"""

def __mod_name__() -> str:
    return "AI Chat"

__handlers__ = [
    CommandHandler(["ai", "aichat"], toggle_ai_chat, run_async=True),
    CommandHandler("chat", chat_with_ai, run_async=True),
    MessageHandler(
        Filters.text & ~Filters.command & Filters.reply,
        chat_with_ai,
        run_async=True
    )
]
