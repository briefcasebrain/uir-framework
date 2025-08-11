"""Mock database for testing without PostgreSQL"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import json
import uuid


class MockDatabase:
    """Mock database that stores data in memory"""
    
    def __init__(self):
        self.tables = {
            "users": {},
            "providers": {},
            "query_history": {},
            "usage_metrics": [],
            "api_keys": {},
            "sessions": {}
        }
        self.sequences = {
            "usage_metrics_id": 0
        }
    
    async def initialize(self):
        """Initialize database (create tables)"""
        # Simulate database connection
        await asyncio.sleep(0.01)
        
        # Add some default data
        await self._add_default_data()
    
    async def _add_default_data(self):
        """Add default test data"""
        # Add default providers
        default_providers = [
            {
                "id": str(uuid.uuid4()),
                "name": "google",
                "type": "search_engine",
                "config": {
                    "api_key": "test-google-key",
                    "cx": "test-search-engine"
                },
                "status": "active",
                "created_at": datetime.now()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "pinecone",
                "type": "vector_db",
                "config": {
                    "api_key": "test-pinecone-key",
                    "environment": "us-west1-gcp"
                },
                "status": "active",
                "created_at": datetime.now()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "elasticsearch",
                "type": "document_store",
                "config": {
                    "host": "localhost",
                    "port": 9200,
                    "use_ssl": False
                },
                "status": "active",
                "created_at": datetime.now()
            }
        ]
        
        for provider in default_providers:
            self.tables["providers"][provider["id"]] = provider
    
    # User operations
    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user"""
        user_id = str(uuid.uuid4())
        user_data["id"] = user_id
        user_data["created_at"] = datetime.now()
        user_data["updated_at"] = datetime.now()
        
        self.tables["users"][user_id] = user_data
        return user_id
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        return self.tables["users"].get(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        for user in self.tables["users"].values():
            if user.get("email") == email:
                return user
        return None
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user data"""
        if user_id in self.tables["users"]:
            self.tables["users"][user_id].update(updates)
            self.tables["users"][user_id]["updated_at"] = datetime.now()
            return True
        return False
    
    # Provider operations
    async def create_provider(self, provider_data: Dict[str, Any]) -> str:
        """Create a new provider"""
        provider_id = str(uuid.uuid4())
        provider_data["id"] = provider_id
        provider_data["created_at"] = datetime.now()
        provider_data["updated_at"] = datetime.now()
        
        self.tables["providers"][provider_id] = provider_data
        return provider_id
    
    async def get_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get provider by ID"""
        return self.tables["providers"].get(provider_id)
    
    async def get_provider_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get provider by name"""
        for provider in self.tables["providers"].values():
            if provider.get("name") == name:
                return provider
        return None
    
    async def list_providers(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all providers"""
        providers = list(self.tables["providers"].values())
        if status:
            providers = [p for p in providers if p.get("status") == status]
        return providers
    
    async def update_provider(self, provider_id: str, updates: Dict[str, Any]) -> bool:
        """Update provider data"""
        if provider_id in self.tables["providers"]:
            self.tables["providers"][provider_id].update(updates)
            self.tables["providers"][provider_id]["updated_at"] = datetime.now()
            return True
        return False
    
    # API Key operations
    async def create_api_key(self, key_data: Dict[str, Any]) -> str:
        """Create API key record"""
        key_id = str(uuid.uuid4())
        key_data["id"] = key_id
        key_data["created_at"] = datetime.now()
        key_data["last_used"] = None
        key_data["usage_count"] = 0
        
        self.tables["api_keys"][key_id] = key_data
        return key_id
    
    async def get_api_key_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        """Get API key by hash"""
        for key_data in self.tables["api_keys"].values():
            if key_data.get("key_hash") == key_hash:
                return key_data
        return None
    
    async def update_api_key_usage(self, key_id: str) -> bool:
        """Update API key usage statistics"""
        if key_id in self.tables["api_keys"]:
            self.tables["api_keys"][key_id]["last_used"] = datetime.now()
            self.tables["api_keys"][key_id]["usage_count"] += 1
            return True
        return False
    
    # Query history operations
    async def log_query(self, query_data: Dict[str, Any]) -> str:
        """Log a query"""
        query_id = str(uuid.uuid4())
        query_data["id"] = query_id
        query_data["timestamp"] = datetime.now()
        
        self.tables["query_history"][query_id] = query_data
        return query_id
    
    async def get_query_history(
        self, 
        user_id: str, 
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get query history for user"""
        user_queries = [
            q for q in self.tables["query_history"].values()
            if q.get("user_id") == user_id
        ]
        
        # Sort by timestamp descending
        user_queries.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return user_queries[offset:offset + limit]
    
    # Usage metrics operations
    async def log_usage(self, usage_data: Dict[str, Any]) -> int:
        """Log usage metrics"""
        self.sequences["usage_metrics_id"] += 1
        metric_id = self.sequences["usage_metrics_id"]
        
        usage_data["id"] = metric_id
        usage_data["timestamp"] = datetime.now()
        
        self.tables["usage_metrics"].append(usage_data)
        return metric_id
    
    async def get_usage_stats(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get usage statistics"""
        metrics = self.tables["usage_metrics"]
        
        # Filter by user
        if user_id:
            metrics = [m for m in metrics if m.get("user_id") == user_id]
        
        # Filter by date range
        if start_date:
            metrics = [m for m in metrics if m["timestamp"] >= start_date]
        if end_date:
            metrics = [m for m in metrics if m["timestamp"] <= end_date]
        
        # Aggregate statistics
        total_requests = len(metrics)
        total_tokens = sum(m.get("tokens_used", 0) for m in metrics)
        
        by_provider = {}
        by_operation = {}
        
        for metric in metrics:
            provider = metric.get("provider", "unknown")
            operation = metric.get("operation", "unknown")
            
            by_provider[provider] = by_provider.get(provider, 0) + 1
            by_operation[operation] = by_operation.get(operation, 0) + 1
        
        return {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "by_provider": by_provider,
            "by_operation": by_operation,
            "period_start": start_date,
            "period_end": end_date
        }
    
    # Utility operations
    async def health_check(self) -> Dict[str, Any]:
        """Database health check"""
        return {
            "status": "healthy",
            "tables": {
                table: len(data) if isinstance(data, (dict, list)) else 1
                for table, data in self.tables.items()
            },
            "uptime": "mock_database"
        }
    
    async def clear_table(self, table_name: str) -> bool:
        """Clear a table (for testing)"""
        if table_name in self.tables:
            if isinstance(self.tables[table_name], dict):
                self.tables[table_name].clear()
            elif isinstance(self.tables[table_name], list):
                self.tables[table_name].clear()
            return True
        return False
    
    async def backup_data(self) -> Dict[str, Any]:
        """Create backup of all data"""
        backup = {}
        for table, data in self.tables.items():
            if isinstance(data, dict):
                backup[table] = {k: v for k, v in data.items()}
            elif isinstance(data, list):
                backup[table] = [item for item in data]
            else:
                backup[table] = data
        
        return {
            "tables": backup,
            "sequences": self.sequences.copy(),
            "timestamp": datetime.now()
        }
    
    async def restore_data(self, backup: Dict[str, Any]) -> bool:
        """Restore data from backup"""
        try:
            self.tables = backup["tables"]
            self.sequences = backup.get("sequences", {"usage_metrics_id": 0})
            return True
        except Exception:
            return False