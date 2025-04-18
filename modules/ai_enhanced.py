from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters
from telegram.error import BadRequest

import google.generativeai as genai
from config import Config
from .helper_funcs.chat_status import user_admin
from .sql import ai_sql as sql

# Configure Gemini
genai.configure(api_key=Config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

DEFAULT_PROMPT = """You are a helpful assistant in a Telegram group chat. 
Keep responses concise and friendly. If you don't know something, say so.
Avoid harmful or inappropriate content."""

async def get_ai_response(prompt: str, message: str) -> str:
    """Get response from Gemini API"""
    try:
        response = await model.generate_content(
            f"{prompt}\n\nUser message: {message}"
        )
        return response.text
    except Exception as e:
        return f"Error getting AI response: {str(e)}"

async def moderate_content(text: str) -> dict:
    """Use Gemini to check content for toxicity"""
    try:
        prompt = """Analyze the following text for:
        1. Toxicity
        2. Spam
        3. Harassment
        Return only a JSON with these boolean fields and a reason if any are true."""
        
        response = await model.generate_content(f"{prompt}\n\nText: {text}")
        return eval(response.text)  # Convert string response to dict
    except:
        return {"toxic": False, "spam": False, "harassment": False}

async def translate_text(text: str, target_lang: str) -> str:
    """Translate text to target language"""
    try:
        prompt = f"Translate the following text to {target_lang}:"
        response = await model.generate_content(f"{prompt}\n\n{text}")
        return response.text
    except Exception as e:
        return f"Translation error: {str(e)}"

async def summarize_chat(messages: list) -> str:
    """Summarize chat messages"""
    try:
        chat_text = "\n".join(messages)
        prompt = "Provide a brief summary of this chat conversation:"
        response = await model.generate_content(f"{prompt}\n\n{chat_text}")
        return response.text
    except Exception as e:
        return f"Summarization error: {str(e)}"

async def solve_doubt(text: str) -> str:
    """Get detailed explanation for a doubt/question"""
    try:
        prompt = """You are a knowledgeable tutor. Explain the following doubt/question in detail:
        1. Give a clear explanation
        2. Include relevant examples if applicable
        3. Break down complex concepts
        4. Suggest related topics to explore
        Keep the response concise but informative."""
        
        response = await model.generate_content(f"{prompt}\n\nQuestion: {text}")
        return response.text
    except Exception as e:
        return f"Error solving doubt: {str(e)}"

@user_admin
async def translate_cmd(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    
    if not message.reply_to_message:
        message.reply_text("Reply to a message to translate it!")
        return
        
    args = context.args
    if not args:
        message.reply_text("Specify the target language! Example: /translate es")
        return
        
    target_lang = args[0]
    text = message.reply_to_message.text
    if not text:
        message.reply_text("Can only translate text messages!")
        return
        
    translated = await translate_text(text, target_lang)
    message.reply_text(f"Translation ({target_lang}):\n{translated}")

@user_admin
async def summarize_cmd(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    
    # Get last 20 messages
    messages = []
    async for msg in context.bot.iter_message_history(chat.id, limit=20):
        if msg.text:
            messages.append(f"{msg.from_user.first_name}: {msg.text}")
            
    if not messages:
        message.reply_text("No messages to summarize!")
        return
        
    summary = await summarize_chat(messages)
    message.reply_text(f"Chat Summary:\n\n{summary}")

async def moderate_message(update: Update, context: CallbackContext) -> None:
    """Auto-moderate messages using AI"""
    message = update.effective_message
    chat = update.effective_chat
    
    if not message.text:
        return
        
    settings = sql.get_ai_settings(chat.id)
    if not settings.get('moderation_enabled'):
        return
        
    analysis = await moderate_content(message.text)
    
    if analysis.get('toxic') or analysis.get('spam') or analysis.get('harassment'):
        try:
            message.delete()
            context.bot.send_message(
                chat.id,
                f"Message from {message.from_user.mention_html()} was removed.\n"
                f"Reason: {analysis.get('reason', 'Violated chat rules')}",
                parse_mode=ParseMode.HTML
            )
        except BadRequest:
            pass

@user_admin
async def doubt_cmd(update: Update, context: CallbackContext) -> None:
    """Handle /doubt command"""
    message = update.effective_message
    
    # Get the question text
    if message.reply_to_message:
        # If replying to a message, use that as the question
        if not message.reply_to_message.text:
            message.reply_text("Can only answer text questions!")
            return
        question = message.reply_to_message.text
    else:
        # Get question from command arguments
        if not context.args:
            message.reply_text(
                "Please provide your question after /doubt or reply to a message.\n"
                "Example: /doubt How does photosynthesis work?"
            )
            return
        question = " ".join(context.args)
    
    # Send "typing" action while processing
    context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action='typing'
    )
    
    # Get AI explanation
    explanation = await solve_doubt(question)
    
    # Format and send response
    response = (
        f"🤔 *Question:*\n{question}\n\n"
        f"📚 *Answer:*\n{explanation}"
    )
    
    message.reply_text(
        response,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    ) 