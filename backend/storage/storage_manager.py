import os
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import UploadFile, HTTPException
from collections import OrderedDict
import asyncio
import aiofiles
from api.schemas import FileInfo, FileUploadResponse
from utils.metrics import MetricsService

class BufferCache:
    def __init__(self, size: int = 1000):
        self.cache: OrderedDict = OrderedDict()
        self.max_size = size
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            self.hits += 1
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        self.misses += 1
        return None
    
    def put(self, key: str, value: Any):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        
        if len(self.cache) > self.max_size:
            # Remove least recently used
            self.cache.popitem(last=False)
    
    def get_hit_ratio(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

class StorageManager:
    def __init__(self):
        self.data_dir = os.getenv("DATA_DIR", "../data")
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE_MB", "100")) * 1024 * 1024
        self.buffer_cache = BufferCache(int(os.getenv("BUFFER_CACHE_SIZE", "1000")))
        self.io_operations = 0
        self.metrics = MetricsService()
        self.allowed_extensions = {'.csv', '.txt', '.dat'}
    
    async def initialize(self):
        os.makedirs(self.data_dir, exist_ok=True)
    
    async def upload_file(self, file: UploadFile, user_id: int) -> FileUploadResponse:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in self.allowed_extensions:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # Check file size
        content = await file.read()
        if len(content) > self.max_file_size:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Create user directory
        user_dir = os.path.join(self.data_dir, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        
        # Check for duplicate filename
        file_path = os.path.join(user_dir, file.filename)
        if os.path.exists(file_path):
            raise HTTPException(status_code=400, detail="File already exists")
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        self.io_operations += 1
        await self.metrics.record_io_operation()
        
        return FileUploadResponse(
            filename=file.filename,
            message="File uploaded successfully"
        )
    
    async def list_user_files(self, user_id: int) -> List[FileInfo]:
        user_dir = os.path.join(self.data_dir, str(user_id))
        files = []
        
        if os.path.exists(user_dir):
            for filename in os.listdir(user_dir):
                if any(filename.endswith(ext) for ext in self.allowed_extensions):
                    file_path = os.path.join(user_dir, filename)
                    stat = os.stat(file_path)
                    files.append(FileInfo(
                        filename=filename,
                        size=stat.st_size,
                        uploaded_at=datetime.fromtimestamp(stat.st_mtime)
                    ))
        
        return files
    
    async def delete_file(self, filename: str, user_id: int) -> dict:
        user_dir = os.path.join(self.data_dir, str(user_id))
        file_path = os.path.join(user_dir, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        os.remove(file_path)
        return {"message": f"File {filename} deleted successfully"}
    
    async def read_page(self, file_path: str, page_number: int, page_size: int = 4096) -> bytes:
        cache_key = f"{file_path}:{page_number}"
        
        # Check cache first
        cached_data = self.buffer_cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Read from disk
        offset = page_number * page_size
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                await f.seek(offset)
                data = await f.read(page_size)
                
            self.io_operations += 1
            await self.metrics.record_io_operation()
            
            # Cache the data
            self.buffer_cache.put(cache_key, data)
            
            return data
        except Exception:
            return b''
    
    async def write_page(self, file_path: str, page_number: int, data: bytes):
        page_size = len(data)
        offset = page_number * page_size
        
        async with aiofiles.open(file_path, 'r+b') as f:
            await f.seek(offset)
            await f.write(data)
        
        # Update cache
        cache_key = f"{file_path}:{page_number}"
        self.buffer_cache.put(cache_key, data)
        
        self.io_operations += 1
        await self.metrics.record_io_operation()
    
    def get_cache_hit_ratio(self) -> float:
        return self.buffer_cache.get_hit_ratio()
    
    def get_io_operations(self) -> int:
        return self.io_operations
