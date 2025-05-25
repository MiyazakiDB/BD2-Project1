import time
import json
import os
import asyncio
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
from api.schemas import MetricsResponse

class MetricsService:
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MetricsService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.metrics_file = "./metrics.json"
            self.query_times = defaultdict(list)
            self.io_operations = defaultdict(int)
            self.total_queries = defaultdict(int)
            self.buffer_cache_stats = defaultdict(dict)
            self.active_tables = defaultdict(set)
            self.recent_queries = defaultdict(lambda: deque(maxlen=1000))
            self._initialized = True
    
    async def record_query(self, execution_time_ms: float, io_ops: int, user_id: int = 0):
        async with self._lock:
            self.query_times[user_id].append(execution_time_ms)
            self.io_operations[user_id] += io_ops
            self.total_queries[user_id] += 1
            
            # Keep only last 1000 query times for memory efficiency
            if len(self.query_times[user_id]) > 1000:
                self.query_times[user_id] = self.query_times[user_id][-1000:]
            
            self.recent_queries[user_id].append({
                "timestamp": datetime.now().isoformat(),
                "execution_time_ms": execution_time_ms,
                "io_operations": io_ops
            })
            
            await self._save_metrics()
    
    async def record_io_operation(self, user_id: int = 0):
        async with self._lock:
            self.io_operations[user_id] += 1
    
    async def update_buffer_cache_stats(self, hit_ratio: float, user_id: int = 0):
        async with self._lock:
            self.buffer_cache_stats[user_id] = {
                "hit_ratio": hit_ratio,
                "updated_at": datetime.now().isoformat()
            }
    
    async def add_active_table(self, table_name: str, user_id: int):
        async with self._lock:
            self.active_tables[user_id].add(table_name)
    
    async def remove_active_table(self, table_name: str, user_id: int):
        async with self._lock:
            self.active_tables[user_id].discard(table_name)
    
    async def get_user_metrics(self, user_id: int) -> MetricsResponse:
        async with self._lock:
            user_query_times = self.query_times.get(user_id, [])
            avg_execution_time = sum(user_query_times) / len(user_query_times) if user_query_times else 0.0
            
            buffer_stats = self.buffer_cache_stats.get(user_id, {})
            hit_ratio = buffer_stats.get("hit_ratio", 0.0)
            
            return MetricsResponse(
                total_queries=self.total_queries.get(user_id, 0),
                avg_execution_time_ms=avg_execution_time,
                total_io_operations=self.io_operations.get(user_id, 0),
                buffer_cache_hit_ratio=hit_ratio,
                active_tables=len(self.active_tables.get(user_id, set()))
            )
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        async with self._lock:
            total_queries = sum(self.total_queries.values())
            total_io_ops = sum(self.io_operations.values())
            
            all_query_times = []
            for user_times in self.query_times.values():
                all_query_times.extend(user_times)
            
            avg_execution_time = sum(all_query_times) / len(all_query_times) if all_query_times else 0.0
            
            return {
                "total_queries": total_queries,
                "total_io_operations": total_io_ops,
                "avg_execution_time_ms": avg_execution_time,
                "active_users": len([uid for uid in self.total_queries.keys() if self.total_queries[uid] > 0]),
                "total_active_tables": sum(len(tables) for tables in self.active_tables.values())
            }
    
    async def get_performance_summary(self, user_id: int, hours: int = 24) -> Dict[str, Any]:
        async with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            user_recent_queries = self.recent_queries.get(user_id, deque())
            
            recent_queries = [
                q for q in user_recent_queries 
                if datetime.fromisoformat(q["timestamp"]) > cutoff_time
            ]
            
            if not recent_queries:
                return {
                    "queries_count": 0,
                    "avg_execution_time_ms": 0.0,
                    "total_io_operations": 0,
                    "peak_execution_time_ms": 0.0,
                    "queries_per_hour": 0.0
                }
            
            execution_times = [q["execution_time_ms"] for q in recent_queries]
            total_io = sum(q["io_operations"] for q in recent_queries)
            
            return {
                "queries_count": len(recent_queries),
                "avg_execution_time_ms": sum(execution_times) / len(execution_times),
                "total_io_operations": total_io,
                "peak_execution_time_ms": max(execution_times),
                "queries_per_hour": len(recent_queries) / hours
            }
    
    async def _save_metrics(self):
        try:
            # Convert defaultdict and sets to regular dict/lists for JSON serialization
            metrics_data = {
                "query_times": dict(self.query_times),
                "io_operations": dict(self.io_operations),
                "total_queries": dict(self.total_queries),
                "buffer_cache_stats": dict(self.buffer_cache_stats),
                "active_tables": {k: list(v) for k, v in self.active_tables.items()},
                "last_updated": datetime.now().isoformat()
            }
            
            os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
        except Exception as e:
            # Log error but don't raise to avoid breaking the application
            print(f"Failed to save metrics: {str(e)}")
    
    async def load_metrics(self):
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                
                self.query_times = defaultdict(list, data.get("query_times", {}))
                self.io_operations = defaultdict(int, data.get("io_operations", {}))
                self.total_queries = defaultdict(int, data.get("total_queries", {}))
                self.buffer_cache_stats = defaultdict(dict, data.get("buffer_cache_stats", {}))
                
                active_tables_data = data.get("active_tables", {})
                self.active_tables = defaultdict(set)
                for k, v in active_tables_data.items():
                    self.active_tables[k] = set(v)
                    
        except Exception as e:
            print(f"Failed to load metrics: {str(e)}")
