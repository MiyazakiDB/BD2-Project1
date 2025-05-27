from typing import List, Any, Dict
from api.schemas import *

class ResponseFormatter:
    @staticmethod
    def format_query_response(
        columns: List[str],
        data: List[List[Any]],
        execution_time: float,
        io_operations: int,
        page: int = 1,
        page_size: int = 50
    ) -> QueryResponse:
        total_rows = len(data)
        total_pages = (total_rows + page_size - 1) // page_size
        
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_rows)
        
        paginated_data = data[start_idx:end_idx] if data else []
        
        return QueryResponse(
            columns=columns,
            data=paginated_data,
            execution_time_ms=execution_time,
            io_operations=io_operations,
            rows_affected=len(paginated_data),
            total_pages=total_pages,
            current_page=page
        )
    
    @staticmethod
    def format_table_data(
        columns: List[str],
        data: List[List[Any]],
        page: int = 1,
        page_size: int = 50
    ) -> PaginatedDataResponse:
        total_rows = len(data)
        total_pages = (total_rows + page_size - 1) // page_size
        
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_rows)
        
        paginated_data = data[start_idx:end_idx] if data else []
        
        return PaginatedDataResponse(
            columns=columns,
            data=paginated_data,
            total_rows=total_rows,
            current_page=page,
            total_pages=total_pages,
            page_size=page_size
        )
