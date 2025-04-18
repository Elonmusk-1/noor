from telegram import Update, ParseMode
from telegram.ext import CallbackContext, Filters, MessageHandler, CommandHandler
from telegram.utils.helpers import mention_html
import google.generativeai as genai  # Import the AI library
from config import Config  # Import the Config class

from .sql import welcome_sql as sql

# Configure Gemini
genai.configure(api_key=Config.GEMINI_API_KEY)

def new_member(update: Update, context: CallbackContext):
    chat = update.effective_chat
    should_welc = sql.get_welc_pref(chat.id)
    
    if not should_welc:
        return

    new_members = update.effective_message.new_chat_members
    for new_mem in new_members:
        # Don't welcome yourself
        if new_mem.id == context.bot.id:
            continue

        # Generate a welcome message using AI
        first_name = new_mem.first_name or "PersonWithNoName"
        mention = mention_html(new_mem.id, first_name)

        # Create a prompt for the AI
        prompt = f"You are Noor. A smart and intellegent kid. Create a warm and friendly welcome message for a new user named {first_name}, using a casual tone and including emojis to make it feel friendly and engaging."

        # Get AI response
        try:
            response = get_ai_response(prompt)  # Assuming you have a function to get AI response
            welcome_message = f"{response} {mention}!"  # Append mention to the AI-generated message
        except Exception as e:
            welcome_message = f"Welcome to the chat, {mention}!"  # Fallback message in case of AI failure

        update.effective_message.reply_text(
            welcome_message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

def get_ai_response(prompt: str) -> str:
    """Get response from Google Gemini API"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error getting AI response: {e}")
        return "Welcome to the chat!"  # Fallback message

def set_welcome(update: Update, context: CallbackContext) -> None:
    """Set the welcome message for the chat."""
    chat = update.effective_chat
    message = update.effective_message
    args = context.args

    if len(args) < 1:
        message.reply_text("Please provide a welcome message.")
        return

    welcome_message = " ".join(args)
    sql.set_welcome(chat.id, welcome_message)
    message.reply_text("Welcome message set!")

def get_welcome(update: Update, context: CallbackContext) -> None:
    """Get the current welcome message."""
    chat = update.effective_chat
    message = update.effective_message

    welcome_message = sql.get_welcome(chat.id)
    if welcome_message:
        message.reply_text(f"Current welcome message: {welcome_message}")
    else:
        message.reply_text("No welcome message set.")

def __help__(update: Update) -> str:
    return """
*Welcome Commands:*
• `/setwelcome <message>`: Set the welcome message for the chat
• `/getwelcome`: Get the current welcome message
"""

def __mod_name__() -> str:
    return "Welcome"

__handlers__ = [
    CommandHandler("setwelcome", set_welcome, filters=Filters.chat_type.groups),
    CommandHandler("getwelcome", get_welcome, filters=Filters.chat_type.groups),
    MessageHandler(  # Add this handler for new members
        Filters.status_update.new_chat_members,
        new_member,
        run_async=True
    )
] 

