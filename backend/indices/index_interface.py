import os
import importlib.util
from typing import Any, List, Dict, Optional, Union
from abc import ABC, abstractmethod
from enum import Enum

class IndexType(Enum):
    AVL = "avl"
    HASH = "hash"
    BTREE = "btree"
    GIN = "gin"
    ISAM = "isam"
    RTREE = "rtree"
    IVF = "ivf"
    ISH = "ish"

class BaseIndex(ABC):
    """Abstract base class for all index implementations"""
    
    @abstractmethod
    def insert(self, key: Any, value: Any) -> bool:
        """Insert a key-value pair into the index"""
        pass
    
    @abstractmethod
    def search(self, key: Any) -> Optional[Any]:
        """Search for a value by key"""
        pass
    
    @abstractmethod
    def delete(self, key: Any) -> bool:
        """Delete a key from the index"""
        pass
    
    @abstractmethod
    def range_search(self, start_key: Any, end_key: Any) -> List[Any]:
        """Search for values in a key range"""
        pass
    
    @abstractmethod
    def save_to_file(self, filepath: str) -> bool:
        """Save index to file"""
        pass
    
    @abstractmethod
    def load_from_file(self, filepath: str) -> bool:
        """Load index from file"""
        pass

class IndexInterface:
    """Interface for managing different types of indices"""
    
    def __init__(self):
        self.index_dir = os.getenv("INDEX_DIR", "../index")
        self.loaded_indices: Dict[str, BaseIndex] = {}
        self._index_classes = {}
        self._load_index_implementations()
    
    def _load_index_implementations(self):
        """Dynamically load index implementations from the index directory"""
        try:
            # Map of index types to their expected file/class names
            index_mappings = {
                IndexType.AVL: ("avl", "AVLIndex"),
                IndexType.HASH: ("hash", "HashIndex"),
                IndexType.BTREE: ("btree", "BTreeIndex"),
                IndexType.GIN: ("gin", "GINIndex"),
                IndexType.ISAM: ("isam", "ISAMIndex"),
                IndexType.RTREE: ("rtree", "RTreeIndex"),
                IndexType.IVF: ("ivf", "IVFIndex"),
                IndexType.ISH: ("ish", "ISHIndex")
            }
            
            for index_type, (filename, class_name) in index_mappings.items():
                try:
                    file_path = os.path.join(self.index_dir, f"{filename}.py")
                    if os.path.exists(file_path):
                        spec = importlib.util.spec_from_file_location(filename, file_path)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            
                            if hasattr(module, class_name):
                                self._index_classes[index_type] = getattr(module, class_name)
                            else:
                                print(f"Warning: Class {class_name} not found in {file_path}")
                    else:
                        print(f"Warning: Index file {file_path} not found")
                        # Create placeholder implementation
                        self._index_classes[index_type] = PlaceholderIndex
                except Exception as e:
                    print(f"Error loading {filename}: {str(e)}")
                    self._index_classes[index_type] = PlaceholderIndex
                    
        except Exception as e:
            print(f"Error loading index implementations: {str(e)}")
            # Set all to placeholder
            for index_type in IndexType:
                self._index_classes[index_type] = PlaceholderIndex
    
    def create_index(self, index_type: IndexType, index_name: str, **kwargs) -> BaseIndex:
        """Create a new index of the specified type"""
        if index_type not in self._index_classes:
            raise ValueError(f"Index type {index_type} not supported")
        
        index_class = self._index_classes[index_type]
        index_instance = index_class(**kwargs)
        
        self.loaded_indices[index_name] = index_instance
        return index_instance
    
    def get_index(self, index_name: str) -> Optional[BaseIndex]:
        """Get a loaded index by name"""
        return self.loaded_indices.get(index_name)
    
    def load_index(self, index_type: IndexType, index_name: str, filepath: str) -> BaseIndex:
        """Load an existing index from file"""
        index_instance = self.create_index(index_type, index_name)
        
        if os.path.exists(filepath):
            index_instance.load_from_file(filepath)
        
        return index_instance
    
    def save_index(self, index_name: str, filepath: str) -> bool:
        """Save an index to file"""
        if index_name not in self.loaded_indices:
            return False
        
        return self.loaded_indices[index_name].save_to_file(filepath)
    
    def delete_index(self, index_name: str) -> bool:
        """Remove an index from memory"""
        if index_name in self.loaded_indices:
            del self.loaded_indices[index_name]
            return True
        return False
    
    def build_index_from_data(
        self, 
        index_type: IndexType, 
        index_name: str, 
        data: List[Dict[str, Any]], 
        key_column: str,
        **kwargs
    ) -> BaseIndex:
        """Build an index from table data"""
        index_instance = self.create_index(index_type, index_name, **kwargs)
        
        for i, row in enumerate(data):
            if key_column in row:
                key = row[key_column]
                # Store row index as value
                index_instance.insert(key, i)
        
        return index_instance
    
    def get_optimal_index_type(self, column_type: str, query_patterns: List[str]) -> IndexType:
        """Suggest optimal index type based on data type and query patterns"""
        
        # Simple heuristics for index selection
        if column_type == "ARRAY[FLOAT]":
            return IndexType.RTREE  # For spatial/array data
        elif "range" in query_patterns or "between" in query_patterns:
            return IndexType.BTREE  # Good for range queries
        elif "equality" in query_patterns:
            return IndexType.HASH   # Fast equality lookups
        elif "text_search" in query_patterns:
            return IndexType.GIN    # For text/array searches
        else:
            return IndexType.BTREE  # Default choice


class PlaceholderIndex(BaseIndex):
    """Placeholder implementation for when actual index classes are not available"""
    
    def __init__(self, **kwargs):
        self.data = {}
        self.name = kwargs.get("name", "placeholder")
    
    def insert(self, key: Any, value: Any) -> bool:
        if key not in self.data:
            self.data[key] = []
        self.data[key].append(value)
        return True
    
    def search(self, key: Any) -> Optional[Any]:
        return self.data.get(key)
    
    def delete(self, key: Any) -> bool:
        if key in self.data:
            del self.data[key]
            return True
        return False
    
    def range_search(self, start_key: Any, end_key: Any) -> List[Any]:
        results = []
        for key, values in self.data.items():
            if start_key <= key <= end_key:
                results.extend(values)
        return results
    
    def save_to_file(self, filepath: str) -> bool:
        try:
            import json
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(self.data, f, default=str)
            return True
        except Exception:
            return False
    
    def load_from_file(self, filepath: str) -> bool:
        try:
            import json
            with open(filepath, 'r') as f:
                self.data = json.load(f)
            return True
        except Exception:
            return False
