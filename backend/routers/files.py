from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from pathlib import Path

from backend.database import get_db, User, File as FileModel
from backend.schemas import File as FileSchema, MultimediaFile
from backend.utils.auth import get_current_active_user
from backend.utils.csv_handler import CSVHandler

router = APIRouter(prefix="/files", tags=["files"])

# Crear el directorio multimedia si no existe
MULTIMEDIA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "multimedia")
os.makedirs(MULTIMEDIA_DIR, exist_ok=True)

def get_user_multimedia_dir(user_id: int):
    """Obtiene el directorio multimedia para un usuario específico"""
    user_dir = os.path.join(MULTIMEDIA_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

@router.post("/upload", response_model=FileSchema)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint para subir archivos CSV.
    Verifica si el archivo ya existe para el usuario y lo guarda en su directorio.
    """
    existing_file = db.query(FileModel).filter(
        FileModel.user_id == current_user.id,
        FileModel.filename == file.filename
    ).first()
    
    if existing_file:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un archivo con el nombre '{file.filename}' para este usuario"
        )
    
    csv_handler = CSVHandler(current_user.id)
    file_path = await csv_handler.save_csv_file(file)
    
    db_file = FileModel(
        filename=file.filename,
        file_path=file_path,
        user_id=current_user.id
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return db_file

@router.post("/multimedia/upload", response_model=MultimediaFile)
async def upload_multimedia_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint para subir un archivo multimedia (imagen o audio).
    Verifica el tipo de archivo, lo guarda en el directorio del usuario y registra sus metadatos.
    """
    
    # Verificar si es una imagen o archivo de audio
    is_image = file.content_type.startswith("image/")
    is_audio = file.content_type.startswith("audio/")
    
    if not (is_image or is_audio):
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten archivos de imagen o audio"
        )
    
    # Obtener el directorio multimedia del usuario
    user_dir = get_user_multimedia_dir(current_user.id)
    
    # Verificar si el archivo ya existe
    existing_file = db.query(FileModel).filter(
        FileModel.user_id == current_user.id,
        FileModel.filename == file.filename
    ).first()
    
    if existing_file:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un archivo con el nombre '{file.filename}' para este usuario"
        )
    
    # Guardar el archivo en el directorio multimedia del usuario
    file_path = os.path.join(user_dir, file.filename)
    
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al guardar el archivo: {str(e)}"
        )
    
    # Crear registro en la base de datos
    file_type = "image" if is_image else "audio"
    
    db_file = FileModel(
        filename=file.filename,
        file_path=file_path,
        file_type=file_type,
        user_id=current_user.id
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return MultimediaFile(
        id=db_file.id,
        filename=db_file.filename,
        file_path=db_file.file_path,
        file_type=file_type,
        uploaded_at=db_file.uploaded_at,
        user_id=db_file.user_id
    )

@router.get("/multimedia", response_model=List[MultimediaFile])
def get_user_multimedia_files(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtiene todos los archivos multimedia para un usuario"""
    files = db.query(FileModel).filter(
        FileModel.user_id == current_user.id,
        FileModel.file_type.in_(["image", "audio"])
    ).all()
    
    return [
        MultimediaFile(
            id=file.id,
            filename=file.filename,
            file_path=file.file_path,
            file_type=file.file_type,
            uploaded_at=file.uploaded_at,
            user_id=file.user_id
        )
        for file in files
    ]

@router.get("/", response_model=List[FileSchema])
def get_user_files(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtiene todos los archivos del usuario actual"""
    files = db.query(FileModel).filter(FileModel.user_id == current_user.id).all()
    return files

@router.get("/{file_id}/preview")
def preview_csv_file(
    file_id: int,
    rows: int = 5,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene una vista previa del contenido de un archivo CSV.
    Permite especificar cuántas filas se mostrarán en la vista previa.
    """
    file = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.user_id == current_user.id
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    csv_handler = CSVHandler(current_user.id)
    return csv_handler.get_csv_preview(file.filename, rows)

@router.post("/{file_id}/import/{table_name}")
def import_csv_to_table(
    file_id: int,
    table_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Importa los datos de un archivo CSV a una tabla existente.
    Requiere el ID del archivo y el nombre de la tabla de destino.
    """
    file = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.user_id == current_user.id
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    csv_handler = CSVHandler(current_user.id)
    import_result = csv_handler.import_csv_to_table(file.filename, table_name)
    return import_result

@router.delete("/{file_id}", response_model=dict)
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Elimina un archivo del directorio del usuario y de la base de datos"""
    
    file = db.query(FileModel).filter(FileModel.id == file_id, FileModel.user_id == current_user.id).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="Archivo no encontrado o no tiene permisos")
    
    try:
        # Si es un archivo CSV, usar el manejador CSV
        if not file.file_type or file.file_type not in ['image', 'audio']:
            csv_handler = CSVHandler(current_user.id)
            csv_handler.delete_file(file.filename)
        # Si es un archivo multimedia, eliminarlo directamente
        else:
            if os.path.exists(file.file_path):
                os.remove(file.file_path)
        
        db.delete(file)
        db.commit()
        
        return {"success": True, "message": f"Archivo {file.filename} eliminado correctamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar archivo: {str(e)}")
