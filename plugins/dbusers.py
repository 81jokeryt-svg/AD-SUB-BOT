# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import motor.motor_asyncio
from config import DB_NAME, DB_URI

class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        # Core user collection reference configurations
        self.col = self.db.users
        self.users_col = self.db.users  # Connected for unified admin commands layout

    def new_user(self, id, name):
        return dict(
            id=int(id),
            user_id=int(id),  # Dual routing keys so payment engine never drops lookups
            name=name,
        )
    
    async def add_user(self, id, name):
        if await self.is_user_exist(id):
            return
        user = self.new_user(id, name)
        await self.col.insert_one(user)
    
    async def is_user_exist(self, id):
        # Checks both standard indexes securely 
        user = await self.col.find_one({
            "$or": [
                {'id': int(id)},
                {'user_id': int(id)}
            ]
        })
        return bool(user)

    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count
    
    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        # Deletes from both identifier maps to completely flush subscription
        await self.col.delete_many({
            "$or": [
                {'id': int(user_id)},
                {'user_id': int(user_id)}
            ]
        })

    # ─── STORE CHANNELS / STORIES METHODS ───
    async def get_stories_by_filter(self, query, skip, limit):
        """Asynchronously fetch filtered items from channels_col"""
        cursor = self.db.channels_col.find(query).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def count_stories_by_filter(self, query):
        """Asynchronously count matching documents from channels_col"""
        return await self.db.channels_col.count_documents(query)

    async def find_single_story(self, query):
        """Asynchronously find one precise document from channels_col"""
        return await self.db.channels_col.find_one(query)


db = Database(DB_URI, DB_NAME)
