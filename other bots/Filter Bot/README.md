# Telegram File Filter Bot

A Telegram bot that filters files from a channel and provides direct download links in button format.

## Features

- Monitors a specific Telegram channel for uploaded files
- Stores file information (name, ID, message link)
- Responds to search queries in groups
- Provides direct download links via buttons
- Supports documents, videos, and audio files

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your credentials:
   - Get `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org)
   - Get `BOT_TOKEN` from [@BotFather](https://t.me/BotFather)
   - Set `CHANNEL_ID` to your channel ID (must be in format -100xxxxxxxxxx)

4. Run the bot:
   ```bash
   python bot.py
   ```

## Usage

1. Add the bot to your channel as an admin
2. Add the bot to any group where you want to use it
3. Upload files to the channel
4. In the group, type the name of the file you're looking for
5. The bot will reply with clickable buttons linking to the matching files

## Notes

- The bot must be an admin in the channel to read messages
- The bot must have message access in groups
- File storage is currently in-memory (will be lost when bot restarts)
- For production use, consider implementing a database

## Future Improvements

- Add database support for persistent storage
- Implement pagination for search results
- Add inline query support
- Create an admin panel
- Add download analytics
- Support multiple channels 