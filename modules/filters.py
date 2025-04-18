import re
from typing import Optional

from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters as TgFilters
from telegram.error import BadRequest

from .helper_funcs.chat_status import user_admin
from .sql import filters_sql as sql

HANDLER_GROUP = 10

def list_handlers(update: Update, context: CallbackContext):
    chat = update.effective_chat
    all_handlers = sql.get_chat_triggers(chat.id)

    if not all_handlers:
        update.effective_message.reply_text("No filters are active here!")
        return

    filter_list = "Active filters in this chat:\n"
    for keyword in all_handlers:
        filter_list += " - {}\n".format(keyword)

    update.effective_message.reply_text(filter_list)

@user_admin
def filters(update: Update, context: CallbackContext):
    try:
        chat = update.effective_chat
        msg = update.effective_message
        args = msg.text.split(None, 2)  # use python's maxsplit to separate Cmd, keyword, and reply_text

        if len(args) < 2:
            msg.reply_text("Please provide a filter keyword!")
            return

        extracted = split_quotes(args[1])
        if len(extracted) < 1:
            msg.reply_text("Please provide a valid filter keyword!")
            return

        # set trigger -> lower, so as to avoid adding duplicate filters with different cases
        keyword = extracted[0].lower()
        
        # Add validation for keyword length
        if len(keyword) > 100:  # arbitrary limit
            msg.reply_text("Filter keyword is too long! Please use a shorter keyword.")
            return

        is_sticker = False
        is_document = False
        is_image = False
        is_voice = False
        is_audio = False
        is_video = False
        is_video_note = False
        media_caption = None
        has_buttons = False

        if len(args) >= 3:
            text = args[2]
            data_type = None
            content = None
            buttons = []

            if msg.reply_to_message:
                if msg.reply_to_message.text:
                    text = msg.reply_to_message.text
                elif msg.reply_to_message.sticker:
                    content = msg.reply_to_message.sticker.file_id
                    is_sticker = True
                    data_type = 'sticker'
                # ... handle other media types similarly

            if not text and not content:
                msg.reply_text("You didn't specify what to reply with!")
                return

            sql.add_filter(chat.id, keyword, text, is_sticker, is_document, is_image, is_audio, is_voice, is_video,
                          is_video_note, buttons)
            msg.reply_text("Handler '{}' added!".format(keyword))

    except Exception as e:
        logger.error(f"Error in filters: {str(e)}")
        msg.reply_text("An error occurred while processing the filter.") 
