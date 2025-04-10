import aiosqlite
import os
import logging
import json
from datetime import datetime

logger = logging.getLogger("database")

class DatabaseManager:
    def __init__(self, db_path="database/autorole.db"):
        self.db_path = db_path
        self.db_type = os.path.basename(db_path).split('.')[0]
        
    async def setup(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            if self.db_type == "autorole":
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS autoroles (
                        guild_id INTEGER,
                        role_id INTEGER,
                        added_by INTEGER,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (guild_id, role_id)
                    )
                ''')
            elif self.db_type == "stickyroles":
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS guild_settings (
                        guild_id INTEGER PRIMARY KEY,
                        is_enabled BOOLEAN DEFAULT 0,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS member_roles (
                        guild_id INTEGER,
                        user_id INTEGER,
                        role_ids TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (guild_id, user_id)
                    )
                ''')
            elif self.db_type == "rolebackup":
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS role_backups (
                        guild_id INTEGER PRIMARY KEY,
                        created_by INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        roles_data TEXT
                    )
                ''')
            
            await db.commit()

    
    async def add_autorole(self, guild_id, role_id, author_id):
        if self.db_type != "autorole":
            logger.error(f"Attempted to use autorole method on {self.db_type} database")
            return False
            
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
        if self.db_type != "autorole":
            logger.error(f"Attempted to use autorole method on {self.db_type} database")
            return False
            
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM autoroles WHERE guild_id = ? AND role_id = ?",
                (guild_id, role_id)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_autoroles(self, guild_id):
        if self.db_type != "autorole":
            logger.error(f"Attempted to use autorole method on {self.db_type} database")
            return []
            
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT role_id FROM autoroles WHERE guild_id = ?",
                (guild_id,)
            )
            roles = await cursor.fetchall()
            return [role[0] for role in roles]
    
    async def clear_autoroles(self, guild_id):
        if self.db_type != "autorole":
            logger.error(f"Attempted to use autorole method on {self.db_type} database")
            return 0
            
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM autoroles WHERE guild_id = ?",
                (guild_id,)
            )
            await db.commit()
            return cursor.rowcount
    
    async def remove_nonexisting_roles(self, guild_id, valid_role_ids):
        if self.db_type != "autorole":
            logger.error(f"Attempted to use autorole method on {self.db_type} database")
            return 0
            
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
            
    async def set_feature_status(self, guild_id, is_enabled):
        if self.db_type != "stickyroles":
            logger.error(f"Attempted to use stickyroles method on {self.db_type} database")
            return False
            
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT is_enabled FROM guild_settings WHERE guild_id = ?",
                (guild_id,)
            )
            result = await cursor.fetchone()
            
            if result is not None and result[0] == is_enabled:
                return False
                
            if result is None:
                await db.execute(
                    "INSERT INTO guild_settings (guild_id, is_enabled) VALUES (?, ?)",
                    (guild_id, is_enabled)
                )
            else:
                await db.execute(
                    "UPDATE guild_settings SET is_enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE guild_id = ?",
                    (is_enabled, guild_id)
                )
                
            await db.commit()
            return True
            
    async def get_feature_status(self, guild_id):
        if self.db_type != "stickyroles":
            logger.error(f"Attempted to use stickyroles method on {self.db_type} database")
            return False
            
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT is_enabled FROM guild_settings WHERE guild_id = ?",
                (guild_id,)
            )
            result = await cursor.fetchone()
            
            return bool(result[0]) if result else False
            
    async def save_member_roles(self, guild_id, user_id, role_ids):
        if self.db_type != "stickyroles":
            logger.error(f"Attempted to use stickyroles method on {self.db_type} database")
            return False
            
        role_json = json.dumps(role_ids)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO member_roles
                (guild_id, user_id, role_ids, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (guild_id, user_id, role_json)
            )
            await db.commit()
            return True
            
    async def get_member_roles(self, guild_id, user_id):
        if self.db_type != "stickyroles":
            logger.error(f"Attempted to use stickyroles method on {self.db_type} database")
            return []
            
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT role_ids FROM member_roles WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id)
            )
            result = await cursor.fetchone()
            
            if not result:
                return []
                
            try:
                return json.loads(result[0])
            except json.JSONDecodeError:
                logger.error(f"Failed to decode role JSON for user {user_id} in guild {guild_id}")
                return []
                
    async def clear_sticky_roles(self, guild_id):
        if self.db_type != "stickyroles":
            logger.error(f"Attempted to use stickyroles method on {self.db_type} database")
            return 0
            
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM member_roles WHERE guild_id = ?",
                (guild_id,)
            )
            await db.commit()
            return cursor.rowcount
    
    
    async def save_role_backup(self, guild_id, user_id, roles_data):
        if self.db_type != "rolebackup":
            logger.error(f"Attempted to use rolebackup method on {self.db_type} database")
            return False
        
        roles_json = json.dumps(roles_data)
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO role_backups
                    (guild_id, created_by, created_at, roles_data)
                    VALUES (?, ?, CURRENT_TIMESTAMP, ?)
                    """,
                    (guild_id, user_id, roles_json)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving role backup: {e}")
            return False
    
    async def backup_exists(self, guild_id):
        if self.db_type != "rolebackup":
            logger.error(f"Attempted to use rolebackup method on {self.db_type} database")
            return False
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT 1 FROM role_backups WHERE guild_id = ?",
                    (guild_id,)
                )
                result = await cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Error checking if backup exists: {e}")
            return False
    
    async def get_role_backup(self, guild_id):
        if self.db_type != "rolebackup":
            logger.error(f"Attempted to use rolebackup method on {self.db_type} database")
            return None
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    """
                    SELECT guild_id, created_by, created_at, roles_data
                    FROM role_backups
                    WHERE guild_id = ?
                    """,
                    (guild_id,)
                )
                result = await cursor.fetchone()
                
                if not result:
                    return None
                
                try:
                    roles_data = json.loads(result['roles_data'])
                    return {
                        'guild_id': result['guild_id'],
                        'created_by': result['created_by'],
                        'created_at': result['created_at'],
                        'roles': roles_data
                    }
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode roles JSON for guild {guild_id}")
                    return None
        except Exception as e:
            logger.error(f"Error getting role backup: {e}")
            return None
    
    async def delete_role_backup(self, guild_id):
        if self.db_type != "rolebackup":
            logger.error(f"Attempted to use rolebackup method on {self.db_type} database")
            return False
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "DELETE FROM role_backups WHERE guild_id = ?",
                    (guild_id,)
                )
                await db.commit()
                success = cursor.rowcount > 0
                return success
        except Exception as e:
            logger.error(f"Error deleting role backup: {e}")
            return False