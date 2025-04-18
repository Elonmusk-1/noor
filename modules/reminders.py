from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.error import BadRequest

from datetime import datetime, timedelta
import re
import time
from .sql import reminders_sql as sql

TIME_REGEX = (
    r'^(?:(?:([01]?\d|2[0-3]):)?([0-5]?\d):)?([0-5]?\d)$'  # HH:MM:SS
    r'|'
    r'^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$'  # 1d2h3m4s
)

def parse_time(time_str: str) -> int:
    """Convert time string to seconds from now"""
    match = re.match(TIME_REGEX, time_str)
    if not match:
        return None
        
    if match.group(1) is not None:  # HH:MM:SS format
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
    else:  # 1d2h3m4s format
        days = int(match.group(4) or 0)
        hours = int(match.group(5) or 0)
        minutes = int(match.group(6) or 0)
        seconds = int(match.group(7) or 0)
        
    total_seconds = (days * 86400) + (hours * 3600) + (minutes * 60) + seconds
    return int(time.time()) + total_seconds

def format_time(timestamp: int) -> str:
    """Format timestamp to readable string"""
    dt = datetime.fromtimestamp(timestamp)
    now = datetime.now()
    
    if dt.date() == now.date():
        return f"today at {dt.strftime('%H:%M')}"
    elif dt.date() == now.date() + timedelta(days=1):
        return f"tomorrow at {dt.strftime('%H:%M')}"
    else:
        return dt.strftime('%Y-%m-%d %H:%M')

def set_reminder(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    args = context.args
    
    if len(args) < 2:
        message.reply_text(
            "Usage: /remind <time> <message>\n"
            "Time formats:\n"
            "- HH:MM:SS (24-hour format)\n"
            "- 1d2h3m4s (days, hours, minutes, seconds)\n"
            "Examples:\n"
            "/remind 1h30m Team meeting\n"
            "/remind 14:30 Lunch break"
        )
        return
        
    time_str = args[0]
    reminder_text = " ".join(args[1:])
    
    # Parse time
    reminder_time = parse_time(time_str)
    if not reminder_time:
        message.reply_text("Invalid time format!")
        return
        
    # Add reminder
    reminder_id = sql.add_reminder(chat.id, user.id, reminder_text, reminder_time)
    
    # Schedule the reminder
    context.job_queue.run_once(
        send_reminder,
        reminder_time - time.time(),
        context={'chat_id': chat.id, 'user_id': user.id, 'reminder_id': reminder_id}
    )
    
    message.reply_text(
        f"✅ Reminder set for {format_time(reminder_time)}:\n"
        f"{reminder_text}"
    )

def list_reminders(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    
    # Get personal reminders
    personal_reminders = sql.get_user_reminders(user.id)
    
    # Get group reminders if in group
    group_reminders = []
    if chat.type != "private":
        group_reminders = sql.get_chat_reminders(chat.id)
    
    if not personal_reminders and not group_reminders:
        message.reply_text("You have no active reminders!")
        return
        
    text = "📅 *Your Reminders:*\n\n"
    
    if personal_reminders:
        text += "*Personal Reminders:*\n"
        for reminder in personal_reminders:
            text += f"• {format_time(reminder.time)}: {reminder.reminder_text}\n"
            
    if group_reminders:
        text += "\n*Group Reminders:*\n"
        for reminder in group_reminders:
            try:
                member = chat.get_member(reminder.user_id)
                name = member.user.full_name
            except BadRequest:
                name = f"User {reminder.user_id}"
            text += f"• {format_time(reminder.time)}: {reminder.reminder_text} (by {name})\n"
            
    message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

def remove_reminder_cmd(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    message = update.effective_message
    args = context.args
    
    if not args or not args[0].isdigit():
        message.reply_text("Please provide the reminder ID to remove!")
        return
        
    reminder_id = int(args[0])
    reminder = sql.get_reminder(reminder_id)
    
    if not reminder:
        message.reply_text("Reminder not found!")
        return
        
    if reminder.user_id != user.id:
        message.reply_text("You can only remove your own reminders!")
        return
        
    if sql.remove_reminder(reminder_id):
        message.reply_text("✅ Reminder removed!")
    else:
        message.reply_text("Failed to remove reminder!")

def send_reminder(context: CallbackContext):
    """Callback for when a reminder is due"""
    job = context.job
    chat_id = job.context['chat_id']
    user_id = job.context['user_id']
    reminder_id = job.context['reminder_id']
    
    reminder = sql.get_reminder(reminder_id)
    if not reminder:
        return
        
    try:
        context.bot.send_message(
            chat_id,
            f"⏰ *Reminder* for {context.bot.get_chat_member(chat_id, user_id).user.mention_html()}:\n"
            f"{reminder.reminder_text}",
            parse_mode=ParseMode.HTML
        )
    except BadRequest:
        pass
        
    # Handle recurring reminders
    if reminder.recurring and reminder.interval:
        new_time = reminder.time + reminder.interval
        sql.update_reminder_time(reminder_id, new_time)
        
        # Schedule next occurrence
        context.job_queue.run_once(
            send_reminder,
            reminder.interval,
            context={'chat_id': chat_id, 'user_id': user_id, 'reminder_id': reminder_id}
        )
    else:
        sql.remove_reminder(reminder_id) 