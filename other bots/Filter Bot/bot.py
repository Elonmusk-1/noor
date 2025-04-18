from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, RPCError, BadMsgNotification
from config import API_ID, API_HASH, BOT_TOKEN, CHANNEL_ID, OWNER_ID
from database import store_file, search_files, get_last_indexed_message, update_last_indexed_message, get_greatest_indexed_message, clear_indexed_files
from commands import register_commands
from owner_commands import register_owner_commands
import asyncio
import os
import time
import logging
from datetime import datetime
import re
import random

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# List of emojis for reactions
REACTION_EMOJIS = ["👍", "👎", "❤️", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🤬", "😢", "🎉", "🤩", "🤮", "💩", "🙏", "👌", "🕊", "🤡", "🥱", "🥴", "😍", "🐳", "❤️‍🔥", "🌚", "🌭", "💯", "🤣", "⚡️", "🍌", "🏆", "💔", "🤨", "😐", "🍓", "🍾", "💋", "🖕", "😈", "😴", "😭", "🤓", "👻", "👨‍💻", "👀", "🎃", "🙈", "😇", "😨", "🤝", "✍️", "🤗", "🫡", "🎅", "🎄", "☃️", "💅", "🤪", "🗿", "🆒", "💘", "🙉", "🦄", "😘", "💊", "🙊", "😎", "👾", "🤷‍♂️", "🤷", "🤷‍♀️", "😡"]

async def delete_message_after_delay(client, message, delay_seconds):
    """
    Delete a message after a specified delay
    """
    try:
        logger.info(f"Scheduling deletion of message {message.id} after {delay_seconds} seconds")
        await asyncio.sleep(delay_seconds)
        try:
            await message.delete()
            logger.info(f"Successfully deleted message {message.id}")
        except Exception as delete_error:
            logger.error(f"Error deleting message {message.id}: {delete_error}")
            # Try alternative deletion method
            try:
                await client.delete_messages(message.chat.id, message.id)
                logger.info(f"Successfully deleted message {message.id} using alternative method")
            except Exception as alt_delete_error:
                logger.error(f"Alternative deletion also failed for message {message.id}: {alt_delete_error}")
    except Exception as e:
        logger.error(f"Error in delete_message_after_delay for message {message.id}: {e}")

# Initialize the bot with increased timeouts and better error handling
app = Client(
    name="file_filter_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    sleep_threshold=60,  # Increased sleep threshold
    workers=4  # Increased number of workers
)

# Global variable to track bot status
bot_running = False

def create_results_keyboard(unique_results, current_page=1, search_query=""):
    """
    Create paginated keyboard markup for search results.
    10 results per page, max 30 pages.
    """
    # Convert dictionary to list for easier slicing
    results_list = list(unique_results.items())
    
    # Calculate total pages
    total_pages = min(30, (len(results_list) + 9) // 10)  # Max 30 pages
    
    # Create buttons list starting with the search query button
    buttons = [
        [InlineKeyboardButton(f"🎬 {search_query}", callback_data="search_query")]
    ]
    
    # Get current page results (10 per page)
    start_idx = (current_page - 1) * 10
    end_idx = start_idx + 10
    current_results = results_list[start_idx:end_idx]
    
    # Add result buttons
    for msg_id, result in current_results:
        file_info = result['file_info']
        matched_terms = result['matched_terms']
        
        # Show what matched (file name or caption)
        match_info = f"🎥 {file_info['file_name']}"
        if file_info['caption']:
            match_info += f"\n📝 {file_info['caption'][:50]}..."
        match_info += f"\n🔍 Matched: {', '.join(matched_terms)}"
        buttons.append([InlineKeyboardButton(match_info, callback_data=f"forward_{file_info['message_id']}")])
    
    # Add navigation buttons
    nav_buttons = []
    
    # Previous page button
    if current_page > 1:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Previous", callback_data=f"page_{current_page-1}_{search_query}")
        )
    
    # Page indicator
    nav_buttons.append(
        InlineKeyboardButton(f"📄 {current_page}/{total_pages}", callback_data="current_page")
    )
    
    # Next page button
    if current_page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"page_{current_page+1}_{search_query}")
        )
    
    buttons.append(nav_buttons)
    
    return InlineKeyboardMarkup(buttons), total_pages

async def handle_pagination(client, callback_query):
    """
    Handle pagination callbacks
    """
    try:
        # Split callback data into parts: page_NUMBER_SEARCHQUERY
        parts = callback_query.data.split("_", 2)
        if len(parts) != 3:
            await callback_query.answer("Invalid pagination data")
            return
            
        new_page = int(parts[1])
        search_query = parts[2]
        
        results = search_files(search_query)
        
        if not results:
            await callback_query.answer("No results found.")
            return
            
        # Group results by message_id
        unique_results = {}
        for filename, file_info in results:
            if file_info['message_id'] not in unique_results:
                unique_results[file_info['message_id']] = {
                    'file_info': file_info,
                    'matched_terms': [filename]
                }
            else:
                unique_results[file_info['message_id']]['matched_terms'].append(filename)
        
        # Create keyboard for new page
        keyboard, total_pages = create_results_keyboard(unique_results, new_page, search_query)
        
        # Format the message with user mention and search query
        response_text = (
            f"Hey {callback_query.from_user.mention} 👋🏻‎ ‌‎\n\n"
            f"⭕️Rotate your 🔄 phone to see files' full name.......................................⭕️\n\n"
            f"Title : {search_query}\n"
            f"Your Files is Ready Now"
        )
        
        # Edit message with new keyboard
        await callback_query.message.edit_text(
            response_text,
            reply_markup=keyboard
        )
        
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error in pagination: {e}")
        await callback_query.answer("Error changing page.")

async def handle_file_forward(client, callback_query):
    """
    Handle file forwarding when user clicks on a file button
    """
    try:
        # Extract message ID from callback data
        message_id = int(callback_query.data.split("_")[1])
        
        # Get the original message from the channel
        message = await client.get_messages(CHANNEL_ID, message_ids=message_id)
        if not message:
            await callback_query.answer("❌ Could not find the file. Please try again.", show_alert=True)
            return
            
        # Clean up caption if it exists
        caption = message.caption or ""
        if caption:
            # Remove any links or usernames
            caption = re.sub(r'https?://\S+|@\w+', '', caption)
            # Add warning text
            caption = f"{caption}\n\n⚠️ ❌👉This file automatically❗delete after 10 minute❗so please forward in another chat👈❌"
        else:
            # Add the default caption if there's no caption
            caption = "⚠️ ❌👉This file automatically❗delete after 10 minute❗so please forward in another chat👈❌"
            
        # Forward the message to the user without forward tag
        await client.copy_message(
            chat_id=callback_query.from_user.id,
            from_chat_id=CHANNEL_ID,
            message_id=message_id,
            caption=caption
        )
        
        await callback_query.answer("✅ File sent to your private chat!")
        
    except Exception as e:
        logger.error(f"Error forwarding file: {e}")
        await callback_query.answer("❌ Error forwarding file. Please try again.", show_alert=True)

@app.on_callback_query()
async def handle_callback(client, callback_query):
    try:
        # Handle pagination callbacks
        if callback_query.data.startswith("page_"):
            await handle_pagination(client, callback_query)
            return
            
        # Handle file forwarding callbacks
        if callback_query.data.startswith("forward_"):
            await handle_file_forward(client, callback_query)
            return
            
        # Handle membership check callback
        if callback_query.data == "check_membership":
            is_member = await check_channel_membership(client, callback_query.from_user.id)
            if not is_member:
                await callback_query.answer("❌ Please join the channel first!", show_alert=True)
                return
                
            # Get the original search query from the current message text
            current_message = callback_query.message
            if not current_message:
                await callback_query.answer("❌ Could not find original message. Please search again.", show_alert=True)
                return
                
            # Get the original search query from the reply_to_message
            original_message = current_message.reply_to_message
            if not original_message:
                await callback_query.answer("❌ Could not find original message. Please search again.", show_alert=True)
                return
                
            # Get the original search query
            search_query = original_message.text.strip()
            results = search_files(search_query)
            
            if not results:
                await callback_query.message.edit_text("No videos found matching your search.")
                return
                
            # Group results by message_id to avoid duplicates
            unique_results = {}
            for filename, file_info in results:
                if file_info['message_id'] not in unique_results:
                    unique_results[file_info['message_id']] = {
                        'file_info': file_info,
                        'matched_terms': [filename]
                    }
                else:
                    unique_results[file_info['message_id']]['matched_terms'].append(filename)
                    
            # Create paginated keyboard for first page
            keyboard, total_pages = create_results_keyboard(unique_results, 1, search_query)
            
            # Format the message with user mention and search query
            response_text = (
                f"Hey {original_message.from_user.mention} 👋🏻‎ ‌‎\n\n"
                f"⭕️Rotate your 🔄 phone to see files' full name.......................................⭕️\n\n"
                f"Title : {search_query}\n"
                f"Your Files is Ready Now"
            )
            
            await callback_query.message.edit_text(
                response_text,
                reply_markup=keyboard
            )
            
            await callback_query.answer("✅ Welcome! You can now access the files.", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")
        await callback_query.answer("❌ An error occurred. Please try again.", show_alert=True)

@app.on_message(filters.command('start'))
async def start_command(client, message):
    try:
        logger.info(f"Received /start command from {message.from_user.id}")
        
        # Send the start message
        await message.reply(
            "Hi! I'm a file filter bot. I can help you find files from the channel.\n\n"
            "To use me:\n"
            "1. Add me to your channel as admin\n"
            "2. Add me to any group\n"
            "3. In the group, type the name of the file you're looking for\n"
            "4. I'll reply with clickable buttons to download the files"
        )
        logger.info("Start message sent successfully")
        
    except BadMsgNotification as e:
        if e.x == 16:  # Time sync error
            logger.warning("Time synchronization error in start command")
            await asyncio.sleep(1)  # Wait a bit before retrying
            await start_command(client, message)  # Retry
    except FloodWait as e:
        logger.warning(f"FloodWait in start command: {e}")
        await asyncio.sleep(e.value)
        await start_command(client, message)
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        try:
            await message.reply("An error occurred. Please try again later.")
        except Exception as reply_error:
            logger.error(f"Failed to send error message: {str(reply_error)}")

async def check_channel_membership(client, user_id):
    """
    Check if a user is a member of the channel.
    Returns True if member, False if not.
    """
    try:
        member = await client.get_chat_member(CHANNEL_ID, user_id)
        return member.status not in ["left", "kicked", "banned"]
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        return False

def create_channel_join_keyboard():
    """
    Create keyboard with channel join button and start button
    """
    channel_link = "https://t.me/+rKi9gInILoE5YTlh"  # Direct invite link
    buttons = [
        [InlineKeyboardButton("🎬 Join Channel", url=channel_link)],
        [InlineKeyboardButton("🔄 Try Again", callback_data="check_membership")]
    ]
    return InlineKeyboardMarkup(buttons)

def contains_only_symbols(text):
    """
    Check if the text contains only symbols and no alphanumeric characters
    """
    # Remove whitespace first
    text = text.strip()
    # If empty after stripping, return True
    if not text:
        return True
    # Check if there are any alphanumeric characters
    return not bool(re.search(r'[a-zA-Z0-9]', text))

def clean_search_text(text):
    """
    Clean search text by removing symbols and extra spaces
    """
    # Remove all symbols except spaces
    cleaned = re.sub(r'[^\w\s]', '', text)
    # Remove extra spaces and convert to lowercase
    cleaned = ' '.join(cleaned.split()).lower()
    return cleaned

@app.on_message(filters.private & filters.text & ~filters.bot)
async def handle_private_message(client, message):
    try:
        # Check if message contains only symbols
        if contains_only_symbols(message.text):
            return
        
        # Check if the message is a command
        if message.text.startswith('/'):
            # Let the command handlers handle it
            return
            
        # First check if user is member of the channel
        is_member = await check_channel_membership(client, message.from_user.id)
        if not is_member:
            # Reply to the original message so we can reference it later
            response = await message.reply(
                "❌ You need to join our channel to use this bot!\n\n"
                "1️⃣ Join the channel\n"
                "2️⃣ Come back and click 'Try Again'",
                reply_markup=create_channel_join_keyboard(),
                reply_to_message_id=message.id  # Explicitly reply to the original message
            )
            # Schedule deletion of both user message and bot response after 1 minute
            asyncio.create_task(delete_message_after_delay(client, message, 60))
            asyncio.create_task(delete_message_after_delay(client, response, 60))
            return

        logger.info(f"Received private message from {message.from_user.id}: {message.text}")
        # Clean the search query by removing symbols
        search_query = clean_search_text(message.text)
        results = search_files(search_query)

        if not results:
            # Forward the unfound query to the specified group
            try:
                forward_text = (
                    f"🔍 New Search Query\n\n"
                    f"From User: {message.from_user.mention} (ID: {message.from_user.id})\n"
                    f"Query: {message.text}\n"
                    f"Cleaned Query: <code>{search_query}</code>"
                )
                await client.send_message(-1002619242416, forward_text, parse_mode="html")
                logger.info(f"Forwarded unfound query to group: {message.text}")
            except Exception as e:
                logger.error(f"Error forwarding unfound query: {e}")

            response = await message.reply(
                "●I could not find the file you requested😕\n\n"
                "● Is the movie you asked about released OTT..?\n\n"
                "● Pay attention to the following…\n\n"
                "● Ask for correct spelling.\n\n"
                "● Do not ask for movies that are not released on OTT platforms.\n\n"
                "● Also ask [movie name, language] like this..‌‌."
            )
            # Schedule deletion of both user message and bot response after 1 minute
            asyncio.create_task(delete_message_after_delay(client, message, 60))
            asyncio.create_task(delete_message_after_delay(client, response, 60))
            return

        # Group results by message_id to avoid duplicates
        unique_results = {}
        for filename, file_info in results:
            if file_info['message_id'] not in unique_results:
                unique_results[file_info['message_id']] = {
                    'file_info': file_info,
                    'matched_terms': [filename]
                }
            else:
                unique_results[file_info['message_id']]['matched_terms'].append(filename)

        # Create paginated keyboard for first page
        keyboard, total_pages = create_results_keyboard(unique_results, 1, search_query)

        # Format the message with user mention and search query
        response_text = (
            f"Hey {message.from_user.mention} 👋🏻‎ ‌‎\n\n"
            f"⭕️Rotate your 🔄 phone to see files' full name.......................................⭕️\n\n"
            f"Title : {search_query}\n"
            f"Your Files is Ready Now"
        )

        response = await message.reply(
            response_text,
            reply_markup=keyboard,
            reply_to_message_id=message.id  # Explicitly reply to the original message
        )
        # Schedule deletion of both user message and bot response after 1 minute
        asyncio.create_task(delete_message_after_delay(client, message, 60))
        asyncio.create_task(delete_message_after_delay(client, response, 60))
    except BadMsgNotification as e:
        if e.x == 16:
            logger.warning("Time synchronization error in private message")
            await asyncio.sleep(1)
            await handle_private_message(client, message)
    except FloodWait as e:
        logger.warning(f"FloodWait in private message: {e}")
        await asyncio.sleep(e.value)
        await handle_private_message(client, message)
    except Exception as e:
        logger.error(f"Error in private message: {e}")
        response = await message.reply("An error occurred while processing your message.")
        # Schedule deletion of both user message and bot response after 1 minute
        asyncio.create_task(delete_message_after_delay(client, message, 60))
        asyncio.create_task(delete_message_after_delay(client, response, 60))

@app.on_message(filters.chat(CHANNEL_ID) & (filters.document | filters.video | filters.audio | filters.photo))
async def handle_new_file(client, message):
    try:
        logger.info(f"New file detected in channel: {message.id}")
        
        # Get file name based on file type
        if message.document:
            file_name = message.document.file_name
        elif message.video:
            file_name = message.video.file_name or f"video_{message.id}.mp4"
        elif message.audio:
            file_name = message.audio.file_name or f"audio_{message.id}.mp3"
        elif message.photo:
            file_name = f"photo_{message.id}.jpg"
        else:
            return

        # Get caption if exists
        caption = message.caption or ""
        
        # Store both file name and caption
        file_info = {
            "file_id": message.id,
            "message_id": message.id,
            "channel_id": CHANNEL_ID,
            "file_name": file_name.lower(),
            "caption": caption.lower(),
            "timestamp": datetime.now().isoformat(),
            "file_type": message.media.value if hasattr(message, 'media') else 'document'
        }
        
        # Store both file name and caption separately for better search
        store_file(file_name.lower(), file_info)
        if caption:  # Only store caption if it exists
            store_file(caption.lower(), file_info)
            
        logger.info(f"New file indexed: {file_name}")
        if caption:
            logger.info(f"Caption: {caption}")
            
    except BadMsgNotification as e:
        if e.x == 16:  # Time sync error
            logger.warning("Time synchronization error in new file handler")
            await asyncio.sleep(1)  # Wait a bit before retrying
            await handle_new_file(client, message)  # Retry
    except Exception as e:
        logger.error(f"Error handling new file: {e}")

async def check_bot_status():
    """Periodically check if the bot is still running"""
    global bot_running
    while True:
        try:
            if not bot_running:
                logger.warning("Bot is not running, attempting to restart...")
                await restart_bot()
            await asyncio.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Error in status check: {e}")
            await asyncio.sleep(60)

async def restart_bot():
    """Restart the bot if it's not running"""
    global bot_running
    try:
        if not bot_running:
            logger.info("Starting bot...")
            await app.start()
            bot_running = True
            logger.info("Bot started successfully")
    except Exception as e:
        logger.error(f"Error restarting bot: {e}")
        bot_running = False

async def index_existing_files(client):
    """
    Index all existing files in the channel in reverse order (newest to oldest)
    """
    try:
        logger.info("Starting indexing process...")
        
        # Verify channel access first
        try:
            test_message = await client.get_messages(CHANNEL_ID, message_ids=8355)
            if not test_message:
                logger.error("Could not access message ID 8355. Please check channel access and message ID.")
                return "Error: Could not access channel messages"
            logger.info(f"Successfully accessed message ID 8355: {test_message.id}")
        except Exception as e:
            logger.error(f"Error accessing channel: {e}")
            return f"Error accessing channel: {str(e)}"
        
        # Start from message ID 8355
        latest_message_id = 8355
        logger.info(f"Starting indexing from message ID: {latest_message_id}")
        
        # Start from the latest message and work backwards
        current_message_id = latest_message_id
        indexed_count = 0
        video_formats = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v']
        
        while current_message_id > 0:
            try:
                logger.info(f"Processing batch starting from message ID: {current_message_id}")
                
                # Get a batch of messages
                message_ids = list(range(current_message_id, max(0, current_message_id - 100), -1))
                if not message_ids:
                    logger.info("No more message IDs to process")
                    break
                    
                logger.info(f"Fetching messages from ID {message_ids[0]} to {message_ids[-1]}")
                messages = []
                for msg_id in message_ids:
                    try:
                        msg = await client.get_messages(CHANNEL_ID, message_ids=msg_id)
                        if msg:
                            messages.append(msg)
                            # Log progress every 100 messages
                            if len(messages) % 100 == 0:
                                logger.info(f"Processed {len(messages)} messages in current batch")
                    except Exception as e:
                        logger.error(f"Error getting message {msg_id}: {e}")
                        continue
                
                if not messages:
                    logger.info("No messages found in current batch")
                    break
                    
                logger.info(f"Processing {len(messages)} messages for video files")
                for message in messages:
                    if not message:
                        continue
                        
                    # Check if message has a document or video
                    if message.document or message.video:
                        file = message.document or message.video
                        file_name = file.file_name or "unnamed_file"
                        
                        # Check if file is a video format
                        if any(file_name.lower().endswith(fmt) for fmt in video_formats):
                            # Store file information
                            store_file(
                                message_id=message.id,
                                file_name=file_name,
                                caption=message.caption or "",
                                file_type="video"
                            )
                            indexed_count += 1
                            
                            # Update progress every 100 files
                            if indexed_count % 100 == 0:
                                logger.info(f"Indexed {indexed_count} video files...")
                
                # Update current_message_id to the last message's ID
                if messages:
                    current_message_id = messages[-1].id - 1
                    logger.info(f"Moving to next batch. Current message ID: {current_message_id}")
                else:
                    logger.info("No more messages to process")
                    break
                
            except FloodWait as e:
                logger.warning(f"FloodWait: Waiting for {e.value} seconds...")
                await asyncio.sleep(e.value)
            except Exception as e:
                logger.error(f"Error indexing messages: {e}")
                continue
        
        logger.info(f"Indexing complete. Total video files indexed: {indexed_count}")
        return f"Indexing complete. Indexed {indexed_count} video files."
        
    except Exception as e:
        logger.error(f"Error in index_existing_files: {e}")
        return f"Error during indexing: {str(e)}"

async def main():
    global bot_running
    try:
        logger.info("Initializing bot...")
        
        # Check if database is locked
        try:
            logger.info("Checking database connection...")
            # Try to access the database to see if it's locked
            from database import get_db_connection
            db_conn = get_db_connection()
            logger.info("Database connection successful")
        except Exception as db_error:
            logger.error(f"Database connection error: {db_error}")
            logger.error(f"Database error type: {type(db_error)}")
            # Try to provide more information about the error
            if "database is locked" in str(db_error):
                logger.error("Database is locked. This usually happens when another instance of the bot is running.")
                logger.error("Please check if another instance of the bot is running and stop it.")
                logger.error("If no other instance is running, try restarting your computer.")
            raise
        
        # Start the bot
        logger.info("Starting bot client...")
        await app.start()
        
        # Check bot connection status
        try:
            me = await app.get_me()
            logger.info(f"Bot connected successfully. Bot info: {me}")
            logger.info(f"Bot username: @{me.username}")
            logger.info(f"Bot ID: {me.id}")
        except Exception as e:
            logger.error(f"Failed to get bot info: {str(e)}")
            raise
        
        bot_running = True
        logger.info("Bot is running...")
        
        # Register command handlers
        logger.info("Registering standard commands...")
        register_commands(app)
        
        # Register owner commands
        logger.info("Registering owner commands...")
        register_owner_commands(app)
        
        # Log all registered handlers for debugging
        logger.info(f"Total registered handlers: {len(app.dispatcher.groups)}")
        for group_id, handlers in app.dispatcher.groups.items():
            logger.info(f"Handler group {group_id}: {len(handlers)} handlers")
            for handler in handlers:
                logger.info(f"  - Handler: {handler.callback.__name__ if hasattr(handler.callback, '__name__') else 'Unknown'}")
        
        logger.info("All command handlers registered successfully")
        
        # Start the status checker
        asyncio.create_task(check_bot_status())
        
        # Keep the bot running
        await idle()
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details available'}")
        bot_running = False
    finally:
        try:
            if bot_running:
                logger.info("Stopping bot...")
                await app.stop()
                bot_running = False
                logger.info("Bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bot: {str(e)}")

if __name__ == "__main__":
    try:
        logger.info("Starting bot application...")
        app.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user!")
    except Exception as e:
        logger.error(f"Bot stopped due to error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No details available'}") 