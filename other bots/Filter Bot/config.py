import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Channel ID where files are uploaded (must be in format -100xxxxxxxxxx)
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))

# MongoDB configuration
MONGODB_URI = os.getenv("MONGODB_URI")

# Additional configuration
OWNER_ID = os.getenv("OWNER_ID")  # Your Telegram user ID

# Validate required configurations
if not all([API_ID, API_HASH, BOT_TOKEN, CHANNEL_ID, OWNER_ID, MONGODB_URI]):
    raise ValueError("Missing required environment variables. Please check your .env file.") 