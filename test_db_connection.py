import psycopg2
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    try:
        # Get database URL from config
        db_url = Config.DATABASE_URL
        
        logger.info("Attempting to connect to database...")
        
        # Connect to database
        conn = psycopg2.connect(db_url)
        
        logger.info("Successfully connected to database!")
        
        # Create a cursor
        cur = conn.cursor()
        
        # Test query
        cur.execute("SELECT version();")
        version = cur.fetchone()
        logger.info(f"PostgreSQL version: {version}")
        
        # Close cursor and connection
        cur.close()
        conn.close()
        
        logger.info("Database connection test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        raise

if __name__ == "__main__":
    test_connection() 

