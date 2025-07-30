from ai_workspace import Workspace
from ai_workspace import Document
from ai_workspace import WorkspaceSchema, DocumentSchema
import pytest
from ai_workspace.database import MongoDB, Qdrant
import uuid
from langchain_openai import AzureOpenAIEmbeddings


@pytest.fixture
def document_data() -> DocumentSchema:
    """Create a test workspace schema."""
    return DocumentSchema(
        workspace_id="test_workspace",
        file_name="test_file.txt",
        file_mime="text/plain",
        file_suffix=".txt",
    )


@pytest.fixture
def workspace() -> Workspace:
    """Create a test workspace instance."""
    TEST_MONGODB_URL = "mongodb://localhost:37017/aicore"
    TEST_QDRANT_URL = "http://localhost:7333"
    mongodb = MongoDB(uri=TEST_MONGODB_URL)
    qdrant = Qdrant(uri=TEST_QDRANT_URL)
    embedding = AzureOpenAIEmbeddings()

    return Workspace(mongodb=mongodb, qdrant=qdrant, embedding=embedding)


def test_upload_document(workspace, document_data):
    """Test adding a new document."""
    document_id = workspace.document_client.upload_document(document_data)
    assert document_id is not None
    assert isinstance(document_id, str)

    # Find the document in workspace
    found_document = workspace.document_client.get_document(document_id)
    assert found_document is not None
    assert found_document.workspace_id == document_data.workspace_id
    assert found_document.file_name == document_data.file_name
    assert found_document.file_mime == document_data.file_mime
    assert found_document.file_suffix == document_data.file_suffix
