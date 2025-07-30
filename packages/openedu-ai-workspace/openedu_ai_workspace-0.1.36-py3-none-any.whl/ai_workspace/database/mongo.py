from urllib.parse import urlparse

from pymongo import MongoClient
from typing import Optional
from .base import BaseDatabase


class MongoDB(BaseDatabase):
    """A class to manage MongoDB connections and operations."""

    uri: str = "mongodb://localhost:27017"
    client: MongoClient | None = None
    db_name: str | None = None
    _instance: Optional["MongoDB"] = None

    class Config:
        arbitrary_types_allowed = True  # Allow MongoClient

    def get_client(self):
        if not self.client:
            if not self.uri:
                raise ValueError("MongoDB URI is not set.")
            self.client = MongoClient(self.uri)

        return self.client

    def get_db(self):
        _client = self.get_client()
        if not self.db_name:
            # Try get db_name from the URI
            parsed_uri = urlparse(self.uri)
            self.db_name = parsed_uri.path.lstrip("/")
        if not self.db_name:
            raise ValueError("Database name is not set.")
        if self.db_name not in _client.list_database_names():
            raise ValueError(f"Database '{self.db_name}' does not exist.")

        return _client[self.db_name]

    def close(self):
        if self.client:
            self.client.close()
            self.client = None

    def __del__(self):
        """Ensure the MongoDB client is closed when the instance is deleted."""
        self.close()
        self._instance = None
