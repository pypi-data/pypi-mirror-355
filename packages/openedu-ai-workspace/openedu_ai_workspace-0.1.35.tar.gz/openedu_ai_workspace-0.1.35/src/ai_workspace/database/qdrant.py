from .base import BaseDatabase
from typing import Optional
from qdrant_client import QdrantClient


class Qdrant(BaseDatabase):
    """A class to manage Qdrant vector database connections and operations."""

    uri: str = "http://localhost:6333"
    api_key: Optional[str] = None
    https: bool = False
    port: int = 6333
    client: Optional[QdrantClient] = None

    def get_client(self) -> QdrantClient:
        if not self.client:
            if not self.uri:
                raise ValueError("Qdrant URI is not set.")
            self.client = QdrantClient(
                url=self.uri, port=self.port, api_key=self.api_key, https=self.https
            )
        return self.client

    def get_collection(self, collection_name: str):
        """Get the collection client for the specified collection."""
        _client = self.get_client()
        if not _client.collection_exists(collection_name):
            raise ValueError(f"Collection '{collection_name}' does not exist.")
        return _client.get_collection(collection_name)

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
