from ai_workspace.schemas import DocumentSchema
from ai_workspace.database import MongoDB
from .base import BaseDocument
from ai_workspace.exceptions import handle_exceptions
from ai_workspace.utils.logger import setup_logger
from typing import ClassVar
import uuid


class Document(BaseDocument):
    mongodb: MongoDB
    document_collection: str = "documents"
    logger: ClassVar = setup_logger(__name__)

    @property
    def collection(self):
        """Get the collection client for the document collection."""
        return self.mongodb.get_db().get_collection(self.document_collection)

    @handle_exceptions
    def upload_document(self, document_data: DocumentSchema):
        """Upload a document to the database.
        Args:
            document_data (DocumentSchema): The document data to upload.

        Returns:
            str: The ID of the uploaded document.
        """
        document_data.document_id = (
            str(uuid.uuid4())
            if not document_data.document_id
            else document_data.document_id
        )
        documents_dict = document_data.model_dump(by_alias=True)
        self.logger.debug("Uploading document with data: %s", documents_dict)
        self.collection.insert_one(documents_dict)
        return document_data.document_id

    @handle_exceptions
    def get_document(self, document_id: str) -> DocumentSchema | None:
        """Retrieve a document by its ID."""
        document = self.collection.find_one({"document_id": document_id})
        self.logger.debug("Retrieved document: %s", document)
        return DocumentSchema(**document) if document else None

    @handle_exceptions
    def delete_document(self, document_id: str) -> bool:
        """Delete a document by its ID."""
        result = self.collection.delete_one({"document_id": document_id})
        return result.deleted_count > 0

    @handle_exceptions
    def list_documents(self, workspace_id: str) -> list[DocumentSchema]:
        """List all documents in a workspace."""
        documents = self.collection.find({"workspace_id": workspace_id})
        return [DocumentSchema(**doc) for doc in documents]
