from database import client

def test_connection():
    try:
        # Test the connection by getting server info
        server_info = client.server_info()
        print("Successfully connected to MongoDB!")
        print(f"Server version: {server_info['version']}")
        print(f"Database name: {client.list_database_names()}")
        return True
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        return False

if __name__ == "__main__":
    test_connection() 