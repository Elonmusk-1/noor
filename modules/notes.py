from telegram import Update, ParseMode
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters
from telegram.error import BadRequest

from .helper_funcs.chat_status import user_admin
from .sql import notes_sql as sql

def get_note(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    
    if len(args) >= 1:
        note_name = args[0].lower()
        note = sql.get_note(chat.id, note_name)
        
        if note:
            try:
                message.reply_text(
                    note.value,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
            except BadRequest as excp:
                if excp.message == "Entity_mention_user_invalid":
                    message.reply_text("Looks like you tried to mention someone I've never seen before.")
                else:
                    raise
        else:
            message.reply_text("This note doesn't exist!")
    else:
        message.reply_text("Get what?")

@user_admin
def save_note(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    args = context.args

    if len(args) >= 2:
        note_name = args[0].lower()
        note_text = " ".join(args[1:])
        
        if sql.add_note(chat.id, note_name, note_text, 1):
            message.reply_text(f"Note {note_name} saved successfully!")
        else:
            message.reply_text("Error saving note!")
    else:
        message.reply_text("You need to give me a note name and the note content!")

@user_admin
def clear_note(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    args = context.args

    if len(args) >= 1:
        note_name = args[0].lower()
        
        if sql.rm_note(chat.id, note_name):
            message.reply_text(f"Note {note_name} deleted!")
        else:
            message.reply_text("That note doesn't exist!")
    else:
        message.reply_text("What note should I delete?")

def list_notes(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    
    notes = sql.get_all_chat_notes(chat.id)
    if notes:
        note_list = "Notes in this chat:\n"
        for note in notes:
            note_list += f" • `{note.name}`\n"
        message.reply_text(note_list, parse_mode=ParseMode.MARKDOWN)
    else:
        message.reply_text("No notes in this chat!")

def __help__(update: Update) -> str:
    return """
*Notes Commands:*
• `/note <note_name>`: Get a note by name
• `/save_note <note_name> <note_content>`: Save a new note
• `/clear_note <note_name>`: Delete a note
• `/list_notes`: List all notes in the chat
"""

def __mod_name__() -> str:
    return "Notes"

__handlers__ = [
    CommandHandler("get", get_note),
    CommandHandler("save", save_note),
    CommandHandler("clear", clear_note),
    CommandHandler(["notes", "saved"], list_notes)
] 
