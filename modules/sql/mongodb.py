import os
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

class MongoDB:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[Database] = None
        self._collections: Dict[str, Collection] = {}

    async def init(self, uri: str) -> bool:
        """Initialize MongoDB connection"""
        try:
            self.client = AsyncIOMotorClient(uri)
            self.db = self.client.get_database()
            # Test connection
            await self.client.admin.command('ping')
            return True
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            return False

    def get_collection(self, name: str) -> Collection:
        """Get or create a collection"""
        if name not in self._collections:
            self._collections[name] = self.db[name]
        return self._collections[name]

    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert a single document"""
        result = await self.get_collection(collection).insert_one(document)
        return str(result.inserted_id)

    async def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document"""
        return await self.get_collection(collection).find_one(query)

    async def find_many(self, collection: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find multiple documents"""
        cursor = self.get_collection(collection).find(query)
        return await cursor.to_list(length=None)

    async def update_one(self, collection: str, query: Dict[str, Any], update: Dict[str, Any]) -> bool:
        """Update a single document"""
        result = await self.get_collection(collection).update_one(query, {"$set": update})
        return result.modified_count > 0

    async def delete_one(self, collection: str, query: Dict[str, Any]) -> bool:
        """Delete a single document"""
        result = await self.get_collection(collection).delete_one(query)
        return result.deleted_count > 0

    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

# Create a global instance
mongodb = MongoDB() 