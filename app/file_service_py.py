import aiofiles
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self, base_dir: str = "user_contexts"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
    
    def get_user_dir(self, user_id: str) -> str:
        """Get user-specific directory"""
        user_dir = os.path.join(self.base_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        return user_dir
    
    async def save_json(self, user_id: str, filename: str, data: Dict[str, Any]) -> bool:
        """Save data as JSON file"""
        try:
            user_dir = self.get_user_dir(user_id)
            filepath = os.path.join(user_dir, filename)
            
            # Add timestamp to data
            data["last_updated"] = datetime.now().isoformat()
            
            async with aiofiles.open(filepath, 'w') as f:
                await f.write(json.dumps(data, indent=2, default=str))
            
            logger.debug(f"Saved JSON to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving JSON {filename} for user {user_id}: {e}")
            return False
    
    async def load_json(self, user_id: str, filename: str) -> Optional[Dict[str, Any]]:
        """Load data from JSON file"""
        try:
            user_dir = self.get_user_dir(user_id)
            filepath = os.path.join(user_dir, filename)
            
            if not os.path.exists(filepath):
                return None
            
            async with aiofiles.open(filepath, 'r') as f:
                content = await f.read()
                return json.loads(content)
                
        except Exception as e:
            logger.error(f"Error loading JSON {filename} for user {user_id}: {e}")
            return None
    
    async def log_to_file(self, user_id: str, filename: str, content: str) -> bool:
        """Append content to a log file"""
        try:
            user_dir = self.get_user_dir(user_id)
            filepath = os.path.join(user_dir, filename)
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {content}\n"
            
            async with aiofiles.open(filepath, 'a', encoding='utf-8') as f:
                await f.write(log_entry)
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging to {filename} for user {user_id}: {e}")
            return False
    
    async def read_file(self, user_id: str, filename: str) -> Optional[str]:
        """Read entire file content"""
        try:
            user_dir = self.get_user_dir(user_id)
            filepath = os.path.join(user_dir, filename)
            
            if not os.path.exists(filepath):
                return None
            
            async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                return await f.read()
                
        except Exception as e:
            logger.error(f"Error reading {filename} for user {user_id}: {e}")
            return None
    
    async def list_user_files(self, user_id: str) -> List[str]:
        """List all files for a user"""
        try:
            user_dir = self.get_user_dir(user_id)
            if os.path.exists(user_dir):
                return [f for f in os.listdir(user_dir) if os.path.isfile(os.path.join(user_dir, f))]
            return []
            
        except Exception as e:
            logger.error(f"Error listing files for user {user_id}: {e}")
            return []
    
    async def delete_file(self, user_id: str, filename: str) -> bool:
        """Delete a specific file"""
        try:
            user_dir = self.get_user_dir(user_id)
            filepath = os.path.join(user_dir, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Deleted file {filepath}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting {filename} for user {user_id}: {e}")
            return False