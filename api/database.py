"""
MiniCloud Platform - Database Connection
Manages async database pool and MinIO client
"""
import asyncpg
from minio import Minio
from typing import Optional
from .config import database_config, minio_config


class Database:
    """Database connection manager - Singleton pattern"""
    _instance: Optional["Database"] = None
    _pool: Optional[asyncpg.Pool] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def pool(self) -> Optional[asyncpg.Pool]:
        return self._pool
    
    @property
    def is_connected(self) -> bool:
        return self._pool is not None
    
    async def connect(self) -> None:
        """Initialize database connection pool"""
        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(
                    database_config.url,
                    min_size=database_config.min_connections,
                    max_size=database_config.max_connections
                )
                print("✅ Connected to PostgreSQL")
            except Exception as e:
                print(f"⚠️ Database connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Close database connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None
    
    async def execute(self, query: str, *args):
        """Execute a query"""
        if self._pool:
            return await self._pool.execute(query, *args)
    
    async def fetch(self, query: str, *args):
        """Fetch multiple rows"""
        if self._pool:
            return await self._pool.fetch(query, *args)
        return []
    
    async def fetchrow(self, query: str, *args):
        """Fetch single row"""
        if self._pool:
            return await self._pool.fetchrow(query, *args)
        return None
    
    async def fetchval(self, query: str, *args):
        """Fetch single value"""
        if self._pool:
            return await self._pool.fetchval(query, *args)
        return None


class MinioStorage:
    """MinIO storage manager - Singleton pattern"""
    _instance: Optional["MinioStorage"] = None
    _client: Optional[Minio] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def client(self) -> Optional[Minio]:
        return self._client
    
    @property
    def is_connected(self) -> bool:
        return self._client is not None
    
    def connect(self) -> None:
        """Initialize MinIO client"""
        try:
            self._client = Minio(
                minio_config.endpoint,
                access_key=minio_config.access_key,
                secret_key=minio_config.secret_key,
                secure=minio_config.secure
            )
            print("✅ Connected to MinIO")
        except Exception as e:
            print(f"⚠️ MinIO connection failed: {e}")


# Global instances
db = Database()
storage = MinioStorage()
