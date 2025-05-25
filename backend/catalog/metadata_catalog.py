import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from api.schemas import CreateTableRequest, TableInfo, ColumnDefinition, TableResponse
from storage.file_processor import FileProcessor
from utils.metrics import MetricsService

class MetadataCatalog:
    def __init__(self):
        self.catalog_file = os.getenv("CATALOG_FILE", "./catalog.json")
        self.data_dir = os.getenv("DATA_DIR", "./data")  # Cambiar de "../data" a "./data"
        self.catalog: Dict = {}
        self.file_processor = FileProcessor()
        self.metrics = MetricsService()
    
    async def initialize(self):
        # Crear directorio de datos si no existe
        os.makedirs(self.data_dir, exist_ok=True)
        
        if os.path.exists(self.catalog_file):
            with open(self.catalog_file, 'r') as f:
                self.catalog = json.load(f)
        else:
            self.catalog = {"tables": {}, "users": {}}
            await self._save_catalog()
    
    async def _save_catalog(self):
        os.makedirs(os.path.dirname(self.catalog_file), exist_ok=True)
        with open(self.catalog_file, 'w') as f:
            json.dump(self.catalog, f, indent=2, default=str)
    
    async def create_table(self, table_data: CreateTableRequest, user_id: int) -> TableResponse:
        table_key = f"{user_id}_{table_data.table_name}"
        
        if table_key in self.catalog["tables"]:
            raise ValueError(f"Table {table_data.table_name} already exists")
        
        # El archivo ya viene con la ruta completa desde el endpoint
        file_path = table_data.file_name
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            raise ValueError(f"File {file_path} not found")
        
        # Process file data
        processed_data = await self.file_processor.process_file(file_path, table_data.columns, table_data.has_headers)
        
        # Crear directorio de datos del usuario si no existe
        user_data_dir = os.path.join(self.data_dir, str(user_id))
        os.makedirs(user_data_dir, exist_ok=True)
        
        # Usar rutas absolutas para evitar problemas
        data_file_name = f"{table_key}.dat"
        data_file_path = os.path.join(user_data_dir, data_file_name)
        data_file_path = os.path.abspath(data_file_path)  # Convertir a ruta absoluta
        
        # Save processed data
        await self.file_processor.save_table_data(data_file_path, processed_data)
        
        # Create table metadata
        table_metadata = {
            "name": table_data.table_name,
            "user_id": user_id,
            "file_path": file_path,
            "columns": [col.dict() for col in table_data.columns],
            "row_count": len(processed_data),
            "created_at": datetime.now().isoformat(),
            "data_file": data_file_path,  # Guardar la ruta absoluta
            "indices": {}
        }
        
        # Create indices for columns that specify them
        for col in table_data.columns:
            if col.index_type:
                index_path = await self._create_index(table_key, col.name, col.index_type, processed_data)
                table_metadata["indices"][col.name] = {
                    "type": col.index_type,
                    "path": index_path
                }
        
        self.catalog["tables"][table_key] = table_metadata
        await self._save_catalog()
        
        print(f"Table created successfully. Data file: {data_file_path}")  # Debug
        
        return TableResponse(
            message=f"Table {table_data.table_name} created successfully",
            table_name=table_data.table_name,
            rows_inserted=len(processed_data)
        )
    
    async def _create_index(self, table_key: str, column_name: str, index_type: str, data: List[List]) -> str:
        # This would interface with your existing index implementations
        index_dir = os.getenv("INDEX_DIR", "./index")
        index_file = f"{table_key}_{column_name}_{index_type.lower()}.idx"
        index_path = os.path.join(index_dir, index_file)
        
        # Here you would call the appropriate index creation method
        # from your existing index implementations
        # For now, we'll create a placeholder
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        with open(index_path, 'w') as f:
            f.write(f"Index for {table_key}.{column_name} using {index_type}")
        
        return index_path
    
    async def list_user_tables(self, user_id: int) -> List[TableInfo]:
        user_tables = []
        for table_key, metadata in self.catalog["tables"].items():
            if metadata["user_id"] == user_id:
                columns = [ColumnDefinition(**col) for col in metadata["columns"]]
                user_tables.append(TableInfo(
                    name=metadata["name"],
                    columns=columns,
                    row_count=metadata["row_count"],
                    created_at=datetime.fromisoformat(metadata["created_at"])
                ))
        return user_tables
    
    async def delete_table(self, table_name: str, user_id: int) -> dict:
        table_key = f"{user_id}_{table_name}"
        
        if table_key not in self.catalog["tables"]:
            raise ValueError(f"Table {table_name} not found")
        
        metadata = self.catalog["tables"][table_key]
        
        # Delete data file
        data_file_path = metadata.get("data_file")
        if data_file_path and os.path.exists(data_file_path):
            os.remove(data_file_path)
        
        # Delete index files
        for col_name, index_info in metadata.get("indices", {}).items():
            if os.path.exists(index_info["path"]):
                os.remove(index_info["path"])
        
        # Remove from catalog
        del self.catalog["tables"][table_key]
        await self._save_catalog()
        
        return {"message": f"Table {table_name} deleted successfully"}
    
    def get_table_metadata(self, table_name: str, user_id: int) -> Optional[Dict]:
        table_key = f"{user_id}_{table_name}"
        return self.catalog["tables"].get(table_key)
