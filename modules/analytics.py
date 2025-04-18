from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CommandHandler
from telegram.error import BadRequest

import matplotlib.pyplot as plt
import pandas as pd
from wordcloud import WordCloud
import io
from datetime import datetime, timedelta
import re

from .helper_funcs.chat_status import user_admin
from .sql import analytics_sql as sql

def track_message(update: Update, context: CallbackContext) -> None:
    """Track message statistics"""
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    
    if not message.text or not chat or chat.type == "private":
        return
        
    # Update message count
    today = datetime.now().strftime('%Y-%m-%d')
    sql.update_message_stats(chat.id, user.id, today)
    
    # Update word stats
    words = re.findall(r'\w+', message.text.lower())
    sql.update_word_stats(chat.id, words)

def generate_activity_chart(chat_id: str, days: int = 7) -> io.BytesIO:
    """Generate activity chart"""
    stats = sql.get_chat_stats(chat_id, days)
    
    # Create DataFrame for plotting
    df = pd.DataFrame(stats['daily_stats'], columns=['date', 'messages'])
    df['date'] = pd.to_datetime(df['date'])
    
    # Create plot
    plt.figure(figsize=(10, 6))
    plt.plot(df['date'], df['messages'], marker='o')
    plt.title('Chat Activity Over Time')
    plt.xlabel('Date')
    plt.ylabel('Messages')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    return buf

def generate_word_cloud(chat_id: str) -> io.BytesIO:
    """Generate word cloud image"""
    words = sql.get_word_cloud_data(chat_id)
    
    # Create word frequency dict
    word_freq = {word.word: word.count for word in words}
    
    # Generate word cloud
    wc = WordCloud(width=800, height=400, background_color='white')
    wc.generate_from_frequencies(word_freq)
    
    # Save to buffer
    buf = io.BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout(pad=0)
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    return buf

def chat_stats(update: Update, context: CallbackContext) -> None:
    """Show chat statistics"""
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    
    days = 7
    if args and args[0].isdigit():
        days = int(args[0])
        if days > 30:
            days = 30
    
    stats = sql.get_chat_stats(chat.id, days)
    
    # Format stats message
    text = f"📊 *Chat Statistics (Last {days} days)*\n\n"
    
    # Daily stats
    text += "*Daily Activity:*\n"
    total_messages = 0
    for date, count in stats['daily_stats']:
        text += f"- {date}: {count} messages\n"
        total_messages += count
    
    text += f"\n*Total Messages:* {total_messages}\n"
    
    # Top users
    text += "\n*Top Users:*\n"
    for i, (user_id, count) in enumerate(stats['top_users'], 1):
        try:
            member = chat.get_member(user_id)
            name = member.user.full_name
        except BadRequest:
            name = f"User {user_id}"
        text += f"{i}. {name}: {count} messages\n"
    
    # Send text stats
    message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    # Send activity chart
    chart = generate_activity_chart(chat.id, days)
    message.reply_photo(chart, caption="📈 Activity Chart")
    
    # Send word cloud
    cloud = generate_word_cloud(chat.id)
    message.reply_photo(cloud, caption="☁️ Word Cloud")

def word_stats(update: Update, context: CallbackContext) -> None:
    """Show word usage statistics"""
    chat = update.effective_chat
    message = update.effective_message
    
    words = sql.get_word_cloud_data(chat.id, 20)  # Get top 20 words
    
    if not words:
        message.reply_text("No word statistics available yet!")
        return
        
    text = "📝 *Most Used Words:*\n\n"
    for i, word in enumerate(words, 1):
        text += f"{i}. {word.word}: {word.count} times\n"
        
    message.reply_text(text, parse_mode=ParseMode.MARKDOWN) 