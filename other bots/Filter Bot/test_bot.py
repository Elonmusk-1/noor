from pyrogram import Client, filters
from config import API_ID, API_HASH, BOT_TOKEN
import asyncio

async def main():
    # Initialize the bot
    app = Client(
        "test_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN
    )

    print('Test Bot Started...')

    @app.on_message(filters.private & filters.command('start'))
    async def start_command(client, message):
        print(f"Received /start command from {message.from_user.id}")
        await message.reply("Test bot is working!")

    @app.on_message(filters.private & filters.text)
    async def handle_private_message(client, message):
        print(f"Received private message from {message.from_user.id}: {message.text}")
        await message.reply("Test bot received your message!")

    # Start the bot
    await app.start()
    print("Bot is running...")
    await app.idle()

if __name__ == "__main__":
    asyncio.run(main()) 