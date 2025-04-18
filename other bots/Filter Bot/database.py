from pymongo import MongoClient
import re
from config import MONGODB_URI
from datetime import datetime
import logging
import socket
import sqlite3
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set a longer timeout for DNS resolution
socket.setdefaulttimeout(30)

# MongoDB connection
mongo_client = None
db = None
collection = None

def get_db_connection():
    """
    Get a connection to the database
    This function is used to check if the database is accessible
    """
    global mongo_client, db, collection
    
    # Check if MongoDB connection is already established
    if mongo_client is not None:
        try:
            # Test the connection
            mongo_client.admin.command('ping')
            logger.info("Using existing MongoDB connection")
            return mongo_client
        except Exception as e:
            logger.error(f"Error with existing MongoDB connection: {e}")
            # Reset the connection
            mongo_client = None
            db = None
            collection = None
    
    # Check for SQLite database files that might be locked
    try:
        # Look for SQLite database files in the current directory
        for file in os.listdir('.'):
            if file.endswith('.db') or file.endswith('.sqlite') or file.endswith('.sqlite3'):
                logger.warning(f"Found SQLite database file: {file}")
                try:
                    # Try to connect to the SQLite database
                    conn = sqlite3.connect(file, timeout=1)
                    conn.close()
                    logger.info(f"Successfully connected to SQLite database: {file}")
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e):
                        logger.error(f"SQLite database {file} is locked. This might be causing the issue.")
                        logger.error("Please check if another instance of the bot is running and stop it.")
                        logger.error("If no other instance is running, try restarting your computer.")
                    raise
    except Exception as e:
        logger.error(f"Error checking for SQLite databases: {e}")
        # Continue with MongoDB connection even if SQLite check fails
    
    # Connect to MongoDB with SSL configuration
    try:
        # Parse the MongoDB URI to get the host
        if MONGODB_URI.startswith('mongodb+srv://'):
            # For MongoDB Atlas, use the direct connection string
            mongo_client = MongoClient(MONGODB_URI, 
                               tls=True, 
                               tlsAllowInvalidCertificates=True,
                               serverSelectionTimeoutMS=30000,
                               connectTimeoutMS=30000,
                               socketTimeoutMS=30000)
        else:
            # For regular MongoDB connection
            mongo_client = MongoClient(MONGODB_URI, 
                               serverSelectionTimeoutMS=30000,
                               connectTimeoutMS=30000,
                               socketTimeoutMS=30000)
        
        # Test the connection
        mongo_client.admin.command('ping')
        db = mongo_client['file_filter_bot']
        # Create a new collection for this indexing session
        collection = db['files_index_v2']  # New collection name
        logger.info("Successfully connected to MongoDB")
        return mongo_client
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        raise

# Initialize the database connection
try:
    get_db_connection()
except Exception as e:
    logger.error(f"Failed to initialize database connection: {e}")

def store_file(message_id, file_name, caption, file_type):
    """
    Store file information in the database
    """
    try:
        # Ensure database connection is established
        if collection is None:
            get_db_connection()
            
        # Clean and prepare the file name and caption for searching
        clean_file_name = file_name.lower()
        clean_caption = caption.lower() if caption else ""
        
        # Create searchable text by combining file name and caption
        searchable_text = f"{clean_file_name} {clean_caption}"
        
        # Store in database
        collection.insert_one({
            'message_id': message_id,
            'file_name': file_name,
            'caption': caption,
            'file_type': file_type,
            'searchable_text': searchable_text,
            'indexed_at': datetime.utcnow()
        })
        return True
    except Exception as e:
        logger.error(f"Error storing file: {e}")
        return False

def search_files(query):
    """
    Search for files using improved search functionality
    """
    try:
        # Ensure database connection is established
        if collection is None:
            get_db_connection()
            
        # Convert query to lowercase and split into words
        query_words = query.lower().split()
        
        # Create a regex pattern that matches all words in any order
        # This will match words even if they're separated by other characters
        pattern = '.*'.join([re.escape(word) for word in query_words])
        regex = re.compile(pattern, re.IGNORECASE)
        
        # Search in both file_name and caption
        results = collection.find({
            '$or': [
                {'searchable_text': {'$regex': regex}},
                {'file_name': {'$regex': regex}},
                {'caption': {'$regex': regex}}
            ]
        })
        
        # Convert results to list of tuples (filename, file_info)
        return [(doc['file_name'], {
            'message_id': doc['message_id'],
            'file_name': doc['file_name'],
            'caption': doc['caption'],
            'file_type': doc['file_type']
        }) for doc in results]
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        return []

def get_all_files():
    """Get all stored files"""
    try:
        # Ensure database connection is established
        if collection is None:
            get_db_connection()
            
        cursor = collection.find({})
        return [(doc["filename"], doc["file_info"]) for doc in cursor]
    except Exception as e:
        logger.error(f"Error getting all files from MongoDB: {e}")
        return []

def get_last_indexed_message():
    """
    Get the last indexed message ID
    """
    try:
        # Ensure database connection is established
        if collection is None:
            get_db_connection()
            
        last_doc = collection.find_one(sort=[('message_id', -1)])
        return last_doc['message_id'] if last_doc else None
    except Exception as e:
        logger.error(f"Error getting last indexed message: {e}")
        return None

def update_last_indexed_message(message_id):
    """
    Update the last indexed message ID
    """
    try:
        # Ensure database connection is established
        if collection is None:
            get_db_connection()
            
        collection.update_one(
            {'_id': 'last_indexed'},
            {'$set': {'message_id': message_id}},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Error updating last indexed message: {e}")
        return False

def get_greatest_indexed_message():
    """
    Get the greatest (oldest) indexed message ID
    """
    try:
        # Ensure database connection is established
        if collection is None:
            get_db_connection()
            
        first_doc = collection.find_one(sort=[('message_id', 1)])
        return first_doc['message_id'] if first_doc else None
    except Exception as e:
        logger.error(f"Error getting greatest indexed message: {e}")
        return None

def clear_indexed_files():
    """
    Clear all indexed files from the database
    """
    try:
        # Ensure database connection is established
        if collection is None:
            get_db_connection()
            
        collection.delete_many({})
        logger.info("Successfully cleared all indexed files")
        return True
    except Exception as e:
        logger.error(f"Error clearing indexed files: {e}")
        return False 