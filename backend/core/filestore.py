import os
import shutil
from uuid import UUID
from typing import List, Dict, Any, Optional
import csv
import json
from fastapi import UploadFile, HTTPException, status

from backend.settings import DATA_DIR, UPLOAD_DIR, TABLES_DIR
from backend.db.database import SessionLocal
from backend.db.repositories import FileRepository

class UserFileStore:
    def __init__(self):
        self._ensure_dirs_exist()
        # En producción, usamos base de datos en lugar de memoria
    
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
        
        # Generar nombre de archivo seguro para evitar ataques de traversal
        original_filename = os.path.basename(file.filename)
        
        # Verificar si ya existe un archivo con el mismo nombre para este usuario
        db = SessionLocal()
        try:
            existing_files = FileRepository.get_files_by_owner(db, str(user_id))
            for existing_file in existing_files:
                if existing_file.filename == original_filename:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Un archivo con nombre '{original_filename}' ya existe"
                    )
                    
            file_path = os.path.join(upload_dir, f"{file_id}_{original_filename}")
            
            # Guardar archivo
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Obtener tamaño del archivo
            file_size = os.path.getsize(file_path)
            
            # Almacenar metadatos en la base de datos
            metadata = {
                "id": file_id,
                "owner_id": user_id,
                "filename": original_filename,
                "path": file_path,
                "size": file_size,
                "mime_type": file.content_type or "application/octet-stream"
            }
            
            FileRepository.create_file(db, metadata)
            
            return metadata
        finally:
            db.close()
    
    def get_user_files(self, user_id: UUID) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            files = FileRepository.get_files_by_owner(db, str(user_id))
            return [
                {
                    "id": UUID(file.id),
                    "owner_id": UUID(file.owner_id),
                    "filename": file.filename,
                    "path": file.path,
                    "size": file.size,
                    "mime_type": file.mime_type,
                    "created_at": file.created_at
                }
                for file in files
            ]
        finally:
            db.close()
    
    def get_file_by_id(self, user_id: UUID, file_id: UUID) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            file = FileRepository.get_file_by_id(db, str(file_id), str(user_id))
            
            if not file:
                return None
            
            return {
                "id": UUID(file.id),
                "owner_id": UUID(file.owner_id),
                "filename": file.filename,
                "path": file.path,
                "size": file.size,
                "mime_type": file.mime_type,
                "created_at": file.created_at
            }
        finally:
            db.close()
    
    def delete_file(self, user_id: UUID, file_id: UUID) -> bool:
        db = SessionLocal()
        try:
            file = FileRepository.get_file_by_id(db, str(file_id), str(user_id))
            
            if not file:
                return False
            
            file_path = file.path
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return FileRepository.delete_file(db, str(file_id), str(user_id))
        finally:
            db.close()
    
    def get_csv_reader(self, user_id: UUID, file_id: UUID):
        metadata = self.get_file_by_id(user_id, file_id)
        
        if not metadata:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        file_path = metadata["path"]
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Archivo no encontrado en disco")
        
        if not metadata["mime_type"].startswith("text/csv") and not file_path.endswith(".csv"):
            raise HTTPException(status_code=400, detail="El archivo no es un CSV")
        
        def csv_reader():
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    yield row
        
        return csv_reader()

file_store = UserFileStore()
