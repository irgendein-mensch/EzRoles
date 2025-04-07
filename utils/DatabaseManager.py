import aiosqlite
import os
import logging

logger = logging.getLogger("database")

class DatabaseManager:
    def __init__(self, db_path="database/autorole.db"):
        self.db_path = db_path
        
    async def setup(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS autoroles (
                    guild_id INTEGER,
                    role_id INTEGER,
                    added_by INTEGER,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, role_id)
                )
            ''')
            await db.commit()

    async def add_autorole(self, guild_id, role_id, author_id):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT role_id FROM autoroles WHERE guild_id = ? AND role_id = ?",
                (guild_id, role_id)
            )
            existing_role = await cursor.fetchone()
            
            if existing_role:
                return False
            
            await db.execute(
                "INSERT INTO autoroles (guild_id, role_id, added_by) VALUES (?, ?, ?)",
                (guild_id, role_id, author_id)
            )
            await db.commit()
            return True
    
    async def remove_autorole(self, guild_id, role_id):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM autoroles WHERE guild_id = ? AND role_id = ?",
                (guild_id, role_id)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_autoroles(self, guild_id):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT role_id FROM autoroles WHERE guild_id = ?",
                (guild_id,)
            )
            roles = await cursor.fetchall()
            return [role[0] for role in roles]
    
    async def clear_autoroles(self, guild_id):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM autoroles WHERE guild_id = ?",
                (guild_id,)
            )
            await db.commit()
            return cursor.rowcount
    
    async def remove_nonexisting_roles(self, guild_id, valid_role_ids):
        if not valid_role_ids:
            return await self.clear_autoroles(guild_id)
        
        placeholders = ','.join(['?'] * len(valid_role_ids))
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                f"DELETE FROM autoroles WHERE guild_id = ? AND role_id NOT IN ({placeholders})",
                (guild_id, *valid_role_ids)
            )
            await db.commit()
            return cursor.rowcount