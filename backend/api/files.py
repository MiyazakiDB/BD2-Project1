from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from typing import List
from uuid import UUID, uuid4
from datetime import datetime

from backend.models.user import User
from backend.models.file import File as FileModel, FileList
from backend.core.auth.jwt import get_current_user
from backend.core.filestore import file_store

router = APIRouter()

@router.post("/", response_model=FileModel)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    file_id = uuid4()
    
    # Save file
    metadata = await file_store.save_file(current_user.id, file, file_id)
    
    # Return file info
    return FileModel(
        id=file_id,
        owner_id=current_user.id,
        filename=metadata["filename"],
        mime_type=metadata["mime_type"],
        size=metadata["size"],
        created_at=metadata.get("created_at", datetime.now())
    )

@router.get("/", response_model=FileList)
async def list_files(current_user: User = Depends(get_current_user)):
    user_files = file_store.get_user_files(current_user.id)
    
    file_models = [
        FileModel(
            id=file["id"],
            owner_id=file["owner_id"],
            filename=file["filename"],
            mime_type=file["mime_type"],
            size=file["size"],
            created_at=file.get("created_at", datetime.now())
        ) 
        for file in user_files
    ]
    
    return FileList(files=file_models)

@router.get("/{file_id}", response_class=FileResponse)
async def get_file(
    file_id: UUID,
    current_user: User = Depends(get_current_user)
):
    metadata = file_store.get_file_by_id(current_user.id, file_id)
    
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileResponse(
        path=metadata["path"],
        filename=metadata["filename"],
        media_type=metadata["mime_type"]
    )

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: UUID,
    current_user: User = Depends(get_current_user)
):
    deleted = file_store.delete_file(current_user.id, file_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
