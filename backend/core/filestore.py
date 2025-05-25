import os
import shutil
from uuid import UUID
from typing import List, Dict, Any, Optional
import csv
from fastapi import UploadFile, HTTPException
import json
from pathlib import Path

from backend.settings import DATA_DIR, UPLOAD_DIR, TABLES_DIR

class UserFileStore:
    def __init__(self):
        self._ensure_dirs_exist()
        self._files_metadata: Dict[UUID, Dict[str, Any]] = {}
    
    def _ensure_dirs_exist(self):
        os.makedirs(DATA_DIR, exist_ok=True)
    
    def _get_user_dir(self, user_id: UUID) -> str:
        user_dir = os.path.join(DATA_DIR, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        return user_dir
    
    def _get_user_uploads_dir(self, user_id: UUID) -> str:
        uploads_dir = os.path.join(self._get_user_dir(user_id), UPLOAD_DIR)
        os.makedirs(uploads_dir, exist_ok=True)
        return uploads_dir
    
    def _get_user_tables_dir(self, user_id: UUID) -> str:
        tables_dir = os.path.join(self._get_user_dir(user_id), TABLES_DIR)
        os.makedirs(tables_dir, exist_ok=True)
        return tables_dir
    
    async def save_file(self, user_id: UUID, file: UploadFile, file_id: UUID) -> Dict[str, Any]:
        upload_dir = self._get_user_uploads_dir(user_id)
        
        original_filename = os.path.basename(file.filename)
        file_path = os.path.join(upload_dir, f"{file_id}_{original_filename}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(file_path)
        
        metadata = {
            "id": file_id,
            "owner_id": user_id,
            "filename": original_filename,
            "path": file_path,
            "size": file_size,
            "mime_type": file.content_type or "application/octet-stream"
        }
        self._files_metadata[file_id] = metadata
        
        return metadata
    
    def get_user_files(self, user_id: UUID) -> List[Dict[str, Any]]:
        return [
            metadata for metadata in self._files_metadata.values()
            if metadata["owner_id"] == user_id
        ]
    
    def get_file_by_id(self, user_id: UUID, file_id: UUID) -> Optional[Dict[str, Any]]:
        metadata = self._files_metadata.get(file_id)
        
        if not metadata or metadata["owner_id"] != user_id:
            return None
        
        return metadata
    
    def delete_file(self, user_id: UUID, file_id: UUID) -> bool:
        metadata = self.get_file_by_id(user_id, file_id)
        
        if not metadata:
            return False
        
        file_path = metadata["path"]
        if os.path.exists(file_path):
            os.remove(file_path)
        
        del self._files_metadata[file_id]
        
        return True
    
    def get_csv_reader(self, user_id: UUID, file_id: UUID):
        metadata = self.get_file_by_id(user_id, file_id)
        
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = metadata["path"]
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        if not metadata["mime_type"].startswith("text/csv") and not file_path.endswith(".csv"):
            raise HTTPException(status_code=400, detail="File is not a CSV")
        
        def csv_reader():
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    yield row
        
        return csv_reader()

file_store = UserFileStore()
