from pyrogram import Client, filters
from database import clear_indexed_files
from config import OWNER_ID
import logging

logger = logging.getLogger(__name__)

def register_commands(app):
    """
    Register all command handlers with the bot
    """
    @app.on_message(filters.command('clear') & filters.private)
    async def handle_clear_command(client, message):
        """
        Command to clear all indexed files from the database.
        Only bot owner can use this command.
        """
        try:
            logger.info(f"Clear command received from user {message.from_user.id}")
            logger.info(f"OWNER_ID from config: {OWNER_ID}")
            logger.info(f"Message text: {message.text}")
            
            # Check if the user is the bot owner
            if str(message.from_user.id) != str(OWNER_ID):
                logger.warning(f"Unauthorized clear attempt by user {message.from_user.id}")
                await message.reply("You are not authorized to use this command.")
                return
                
            logger.info(f"Clear command authorized for owner {message.from_user.id}")
            
            # Send initial message
            try:
                status_message = await message.reply("🔄 Clearing all indexed files from database...")
                logger.info("Sent initial status message")
            except Exception as e:
                logger.error(f"Failed to send initial message: {e}")
                return
            
            try:
                # Clear the database
                logger.info("Starting database clear operation")
                success = clear_indexed_files()
                logger.info(f"Database clear operation completed with success={success}")
                
                if success:
                    # Update status message
                    await status_message.edit_text("✅ Successfully cleared all indexed files from database!")
                    logger.info("Sent success message")
                else:
                    await status_message.edit_text("❌ Failed to clear indexed files!")
                    logger.warning("Sent failure message")
            except Exception as e:
                logger.error(f"Error during clearing: {e}")
                try:
                    await status_message.edit_text(f"❌ Error during clearing: {str(e)}")
                except Exception as edit_error:
                    logger.error(f"Failed to edit status message: {edit_error}")
                    try:
                        await message.reply(f"Error during clearing: {str(e)}")
                    except Exception as reply_error:
                        logger.error(f"Failed to send error message: {reply_error}")
                
        except Exception as e:
            logger.error(f"Error in handle_clear_command: {e}")
            try:
                await message.reply("An error occurred while clearing files.")
            except Exception as reply_error:
                logger.error(f"Failed to send error message: {reply_error}") 