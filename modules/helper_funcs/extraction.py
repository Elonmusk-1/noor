from typing import Optional, List
from telegram import Message, MessageEntity
from telegram.error import BadRequest

def extract_user(message: Message, args: List[str]) -> Optional[int]:
    prev_message = message.reply_to_message

    if prev_message:
        user_id = prev_message.from_user.id

    elif len(args) >= 1 and args[0][0] == '@':
        user = args[0]
        try:
            user_id = message.bot.get_chat(user).id
        except BadRequest as excp:
            if excp.message == "Chat not found":
                message.reply_text("I can't find this user.")
                return None
            else:
                raise

    elif len(args) >= 1 and args[0].isdigit():
        user_id = int(args[0])

    else:
        message.reply_text("I can't extract a user from this.")
        return None

    return user_id 
