import logging
import os
from datetime import datetime
import signal
import sys
import logging.handlers

from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler
)

from config import Config
from vars import Vars
from modules import ALL_MODULES
from modules.helper_funcs.chat_status import user_admin
from modules.sql import SESSION
from modules.blacklist import list_blacklist, add_blacklist, remove_blacklist
from modules.groupchat import cmd_groupchat
from modules.group_ai import group_ai_toggle
from modules.cleanservice import toggle_service_messages
from modules.rules import get_rules
from modules.settings import settings
from modules.notes import get_note, save_note, clear_note, list_notes
from modules.backup import backup, restore
from modules.feds import new_fed, join_fed, fed_ban
from modules.welcome import set_welcome, get_welcome  # Import welcome module functions
from modules.karma import check_karma, karma_leaderboard

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Set up file logging
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

file_handler = logging.handlers.RotatingFileHandler(
    filename=os.path.join(log_directory, 'bot.log'),
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MBs
    backupCount=5
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

# Add file handler to root logger
logging.getLogger('').addHandler(file_handler)
logging.getLogger('').setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi! I am a group management bot.')

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    help_text = "*Available Commands:*\n\n"
    keyboard = []

    for module in ALL_MODULES:
        if hasattr(module, "__mod_name__") and hasattr(module, "__help__"):
            mod_name = module.__mod_name__()
            mod_help = module.__help__(update)
            help_text += f"*{mod_name}*\n{mod_help}\n\n"
            keyboard.append([InlineKeyboardButton(mod_name, callback_data=mod_name)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if len(help_text) > 4096:
        # Split help text into multiple messages if too long
        for x in range(0, len(help_text), 4096):
            update.effective_message.reply_text(
                help_text[x:x+4096],
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
    else:
        update.effective_message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

def button(update: Update, context: CallbackContext):
    """Handle button presses."""
    query = update.callback_query
    query.answer()  # Acknowledge the button press

    # Provide explanations based on the button pressed
    command_name = query.data
    for module in ALL_MODULES:
        if hasattr(module, "__mod_name__") and module.__mod_name__() == command_name:
            query.edit_message_text(text=module.__help__(update), parse_mode=ParseMode.MARKDOWN)
            return

def error_handler(update: Update, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    # Log the error before we do anything else, so we can see it even if something breaks
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

def signal_handler(signum, frame):
    logger.info("Received shutdown signal, cleaning up...")
    updater.stop()
    if SESSION:
        SESSION.close()
    sys.exit(0)

def debug_message_handler(update: Update, context: CallbackContext) -> None:
    """Log all messages for debugging"""
    if update.message:
        logger.debug(
            f"=== Debug Message Handler ===\n"
            f"Chat type: {update.effective_chat.type}\n"
            f"Chat ID: {update.effective_chat.id}\n"
            f"Message text: '{update.message.text}'\n"
            f"From user: {update.effective_user.id}\n"
            f"Is reply: {bool(update.message.reply_to_message)}\n"
            f"Has entities: {bool(update.message.entities)}"
        )

def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message for testing."""
    logger.debug(f"Echo handler received: {update.message.text}")
    if update.message.text.lower() == "test":
        update.message.reply_text("Bot is working!")

def main() -> None:
    """Start the bot."""
    global updater  # Make updater global so signal handler can access it
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize configuration
    Config.init()
    
    # Initialize database
    from modules.sql import init
    if not init():
        logger.error("Failed to initialize database. Exiting...")
        return
    
    # Initialize variables
    Vars.init(Config)
    
    # Create the Updater and pass it your bot's token
    updater = Updater(Vars.BOT_TOKEN)
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    # Register module handlers
    logger.info("=== Registering Module Handlers ===")
    for module in ALL_MODULES:
        if hasattr(module, "__handlers__"):
            logger.info(f"Registering handlers for module: {module.__name__}")
            for handler in module.__handlers__:
                try:
                    if isinstance(handler, tuple):  # Handler with group specified
                        h, group = handler
                        dispatcher.add_handler(h, group=group)
                        if isinstance(h, MessageHandler):
                            logger.info(f"Added MessageHandler with filters: {h.filters} in group {group}")
                        elif isinstance(h, CommandHandler):
                            logger.info(f"Added CommandHandler for commands: {h.command} in group {group}")
                    else:  # Regular handler
                        dispatcher.add_handler(handler)
                        if isinstance(handler, MessageHandler):
                            logger.info(f"Added MessageHandler with filters: {handler.filters}")
                        elif isinstance(handler, CommandHandler):
                            logger.info(f"Added CommandHandler for commands: {handler.command}")
                except Exception as e:
                    logger.error(f"Failed to register handler {handler}: {str(e)}")
    
    # Register additional command handlers
    dispatcher.add_handler(CommandHandler("blacklist", list_blacklist))  # Add blacklist command
    dispatcher.add_handler(CommandHandler("addblacklist", add_blacklist))  # Add add to blacklist command
    dispatcher.add_handler(CommandHandler("rmblacklist", remove_blacklist))  # Add remove from blacklist command
    dispatcher.add_handler(CommandHandler("clean", toggle_service_messages))  # Add clean service command
    dispatcher.add_handler(CommandHandler("rules", get_rules))  # Add rules command
    dispatcher.add_handler(CommandHandler("settings", settings))  # Add settings command
    dispatcher.add_handler(CommandHandler("gai", group_ai_toggle))  # Add group AI command
    dispatcher.add_handler(CommandHandler("groupchat", cmd_groupchat))  # Add group chat command
    dispatcher.add_handler(CommandHandler("note", get_note))  # Example for notes
    dispatcher.add_handler(CommandHandler("save_note", save_note))  # Example for saving notes
    dispatcher.add_handler(CommandHandler("clear_note", clear_note))  # Example for clearing notes
    dispatcher.add_handler(CommandHandler("list_notes", list_notes))  # Example for listing notes
    dispatcher.add_handler(CommandHandler("backup", backup))  # Example for backup
    dispatcher.add_handler(CommandHandler("restore", restore))  # Example for restore
    dispatcher.add_handler(CommandHandler("newfed", new_fed))  # Example for creating a new federation
    dispatcher.add_handler(CommandHandler("joinfed", join_fed))  # Example for joining a federation
    dispatcher.add_handler(CommandHandler("fban", fed_ban))  # Example for banning a user in a federation
    dispatcher.add_handler(CommandHandler("setwelcome", set_welcome))  # Set welcome message
    dispatcher.add_handler(CommandHandler("getwelcome", get_welcome))  # Get welcome message
    dispatcher.add_handler(CommandHandler(
        ["karma", "k"], 
        check_karma,
        filters=Filters.chat_type.groups,
        run_async=True
    ))
    
    dispatcher.add_handler(CommandHandler(
        ["karmatop", "ktop"], 
        karma_leaderboard,
        filters=Filters.chat_type.groups,
        run_async=True
    ))
    
    # Register button handler
    dispatcher.add_handler(CallbackQueryHandler(button))
    
    # Register error handler
    dispatcher.add_error_handler(error_handler)
    
    # Register debug message handler
    dispatcher.add_handler(
        MessageHandler(
            Filters.text & ~Filters.command,
            debug_message_handler,
            run_async=True
        ),
        group=100  # Much higher group number means much lower priority
    )
    
    # Register echo handler
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.regex(r'^test$'), echo))
    
    # Start the Bot
    updater.start_polling()
    
    # Run the bot until you press Ctrl-C
    updater.idle()

    # Log registered handlers
    logger.info("=== Registered Handlers ===")
    for group in dispatcher.handlers:
        for handler in dispatcher.handlers[group]:
            if isinstance(handler, MessageHandler):
                logger.info(f"Group {group}: MessageHandler with filters: {handler.filters}")
                if hasattr(handler.filters, 'pattern'):
                    logger.info(f"  Pattern: {handler.filters.pattern}")
            elif isinstance(handler, CommandHandler):
                logger.info(f"Group {group}: CommandHandler for commands: {handler.command}")

    # Log testing handler registration
    logger.info("=== Testing Handler Registration ===")
    for group in dispatcher.handlers:
        for handler in dispatcher.handlers[group]:
            if isinstance(handler, MessageHandler):
                logger.info(f"Group {group}: MessageHandler with filters: {handler.filters}")
                if hasattr(handler.filters, 'pattern'):
                    logger.info(f"  Pattern: {handler.filters.pattern}")
            elif isinstance(handler, CommandHandler):
                logger.info(f"Group {group}: CommandHandler for commands: {handler.command}")

if __name__ == '__main__':
    main() 

