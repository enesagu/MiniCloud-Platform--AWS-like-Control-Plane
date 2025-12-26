"""
MiniCloud Platform - Configuration
Settings and environment variables
"""
import os
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/minicloud")
    min_connections: int = 5
    max_connections: int = 20


@dataclass
class MinioConfig:
    endpoint: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    access_key: str = os.getenv("MINIO_ROOT_USER", "minioadmin")
    secret_key: str = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
    secure: bool = False


@dataclass
class AppConfig:
    title: str = "MiniCloud Platform API"
    description: str = "Self-hosted AWS-like Control Plane API"
    version: str = "1.0.0"
    default_org_id: str = "org-default"
    default_project_id: str = "proj-default"


# Singleton instances
database_config = DatabaseConfig()
minio_config = MinioConfig()
app_config = AppConfig()
