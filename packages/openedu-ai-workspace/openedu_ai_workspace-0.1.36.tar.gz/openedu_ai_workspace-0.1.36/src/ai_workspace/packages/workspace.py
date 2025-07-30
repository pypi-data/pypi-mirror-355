from typing import List, Optional, Union

from langchain_openai import AzureOpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client.models import Distance, PointStruct, VectorParams
from ai_workspace.database import MongoDB, Qdrant

from ai_workspace.schemas import WorkspaceSchema, DocumentSchema
from ai_workspace.exceptions import WorkspaceError, handle_exceptions
from .base import BaseWorkspace
from ai_workspace.utils.logger import setup_logger
from typing import ClassVar
from logging import Logger
import uuid
from ai_workspace.packages.document import Document
from ai_workspace.packages.embed import EmbedDocument
from ai_workspace.packages.cost import CostClient
from ai_workspace.exceptions import (
    WorkspaceAlreadyExistsException,
    WorkspaceNotFoundException,
)


class Workspace(BaseWorkspace):
    """A class to manage vector document storage and retrieval using Qdrant and Azure OpenAI.

    This class provides functionality to store, embed, and retrieve documents using
    Qdrant vector database and Azure OpenAI embeddings.
    """

    mongodb: MongoDB
    workspace_collection: str = "workspaces"
    qdrant: Qdrant
    embedding: AzureOpenAIEmbeddings

    logger: ClassVar[Logger] = setup_logger(__name__)
    vector_config: VectorParams = VectorParams(
        size=3072,  # Size of the embedding vector
        distance=Distance.COSINE,  # Using cosine distance for similarity
    )

    @property
    def document_client(self) -> Document:
        """Get the Document client for managing documents in the workspace."""
        return Document(mongodb=self.mongodb)

    @property
    def embed_client(self) -> EmbedDocument:
        """Get the EmbedDocument client for managing embeddings in the workspace."""
        return EmbedDocument(embedding=self.embedding)

    @property
    def cost_client(self):
        """Get the cost client for managing costs in the workspace."""
        return CostClient(mongodb=self.mongodb)

    @property
    def collection(self):
        """Get the collection client for the workspace collection."""
        return self.mongodb.get_db().get_collection(self.workspace_collection)

    @property
    def qdrant_client(self):
        """Get the Qdrant client."""
        return self.qdrant.get_client()

    def get_vector_store(self, workspace_id: str) -> QdrantVectorStore:
        """Get the vector store for a specific workspace.

        Args:
            workspace_id (str): The ID of the workspace

        Returns:
            QdrantVectorStore: The vector store for the specified workspace
        """
        return QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=workspace_id,
            embedding=self.embed_client.embedding,
        )

    @handle_exceptions
    def get_instructions(self, workspace_id: str) -> str:
        """Get instructions from database schema.

        Args:
            workspace_id (str): The ID of the workspace

        Returns:
            str: The instructions for the workspace

        Raises:
            WorkspaceError: If workspace is not found or has no instructions
        """
        workspace = self.collection.find_one({"workspace_id": workspace_id})
        if not workspace:
            raise WorkspaceError(
                f"Workspace {workspace_id} not found or has no instructions"
            )

        if "instructions" not in workspace:
            raise WorkspaceError(f"Workspace {workspace_id} has no instructions")

        return workspace["instructions"]

    @handle_exceptions
    def create(self, workspace_data: WorkspaceSchema) -> Optional[str]:
        """Add a new workspace to MongoDB.

        Args:
            workspace_data (WorkspaceSchema): Data for the workspace to add

        Returns:
            str: ID of the newly added workspace
        """
        workspace_data.workspace_id = (
            str(uuid.uuid4())
            if not workspace_data.workspace_id
            else workspace_data.workspace_id
        )

        existing_workspace = self.collection.find_one(
            {"workspace_id": workspace_data.workspace_id}
        )
        if existing_workspace:
            raise WorkspaceAlreadyExistsException(workspace_data.workspace_id)

        workspace_dict = workspace_data.model_dump()

        self.collection.insert_one(workspace_dict)

        # Create a Qdrant collection for the workspace
        self.qdrant_client.create_collection(
            collection_name=workspace_data.workspace_id,
            vectors_config=self.vector_config,
        )
        return workspace_data.workspace_id

    def delete_workspace(self, workspace_id: str) -> bool:
        """Delete a workspace from MongoDB.

        Args:
            workspace_id (str): ID of the workspace to delete
            This will also delete the corresponding Qdrant collection.

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            result = self.collection.delete_one({"workspace_id": workspace_id})

            if result.deleted_count > 0:
                self.qdrant_client.delete_collection(workspace_id)
                return True
            else:
                self.logger.warning(f"No workspace found with ID {workspace_id}")
                return False

        except Exception as e:
            self.logger.error(f"ERROR in delete_workspace: {e}")
            return False

    def update_workspace(
        self,
        workspace_id: str,
        instructions: str | None,
        title: str | None,
        description: str | None,
    ) -> bool:
        """Update workspace details for a workspace.

        Args:
            workspace_id (str): ID of the workspace to update
            instructions (str): New instructions for the workspace
            title (str): New title for the workspace
            description (str): New description for the workspace

        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            updates = {}
            if instructions is not None:
                updates["instructions"] = instructions
            if title is not None:
                updates["title"] = title
            if description is not None:
                updates["description"] = description

            result = self.collection.update_one(
                {"workspace_id": workspace_id},
                {"$set": updates},
            )

            if result.modified_count > 0:
                return True
            else:
                raise WorkspaceNotFoundException(workspace_id)

        except Exception as e:
            raise e

    def delete_instructions(self, workspace_id: str) -> bool:
        """Delete instructions for a workspace.

        Args:
            workspace_id (str): ID of the workspace to delete instructions for

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"workspace_id": workspace_id},
                {"$unset": {"instructions": ""}},
            )

            if result.modified_count > 0:
                return True
            else:
                self.logger.warning(f"No workspace found with ID {workspace_id}")
                return False

        except Exception as e:
            self.logger.error(f"ERROR in delete_instructions: {e}")
            return False

    def find_workspace_by_id(self, workspace_id: str) -> Optional[WorkspaceSchema]:
        """Find a workspace by its ID.

        Args:
            workspace_id (str): ID of the workspace to find

        Returns:
            Optional[WorkspaceSchema]: The found workspace or None if not found
        """
        workspace = self.collection.find_one({"workspace_id": workspace_id})
        if not workspace:
            raise WorkspaceNotFoundException(workspace_id)
        return WorkspaceSchema.model_validate(workspace)

    def find_workspace_by_user_id(
        self, user_id: str
    ) -> Optional[List[WorkspaceSchema]]:
        """Find a workspace by its user ID.

        Args:
            user_id (str): ID of the user to find the workspace for

        Returns:
            Optional[WorkspaceSchema]: The found workspace or None if not found
        """
        workspace = self.collection.find({"user_id": user_id})
        if not workspace:
            return None
        return [WorkspaceSchema.model_validate(ws) for ws in workspace]

    @handle_exceptions
    def add_knowledge(
        self,
        document: DocumentSchema,
        raw_texts: Optional[List[str]] = None,
        metadata: Optional[dict | List[dict]] = None,
        to_workspace: bool = True,
    ) -> str:
        """Add a document to the workspace.
        Saves the document to MongoDB and returns its ID.
        Upload the embedded document to the Qdrant collection.
        If `to_workspace` is True, the document will be added to the workspace's collection else it will be added to session collection.
        Args:
            document (DocumentSchema): The document to upload
            raw_texts (Optional[List[str]]): List of raw texts to embed and store
            metadata (Optional[dict | List[dict]]): Metadata for the document.
                If a single dict is provided, it will be applied to all texts.
                If a list of dicts is provided, each text will get its corresponding metadata.

        Returns:
            str: The ID of the uploaded document
        """
        document_id = self.document_client.upload_document(document)
        if not to_workspace and not document.session_id:
            raise WorkspaceError(
                "Cannot add document to session without a session_id in the document"
            )
        if not to_workspace and document.session_id:
            to_collection = document.session_id
        else:
            to_collection = document.workspace_id

        if metadata and isinstance(metadata, dict):
            metadata = [metadata] * len(raw_texts) if raw_texts else []
        if raw_texts:
            points = self.get_vector_store(to_collection).add_texts(
                texts=raw_texts,
                metadatas=(
                    [{"document_id": document_id, **meta} for meta in metadata]
                    if metadata
                    else None
                ),
                ids=[str(uuid.uuid4()) for _ in raw_texts],
            )
            self.logger.debug(
                f"Added {len(points)} points to collection {to_collection} for document {document_id}"
            )
        return document_id
