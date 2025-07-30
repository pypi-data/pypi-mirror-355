from typing import Optional
from pydantic import Field
from .base import BaseSchema


class DocumentSchema(BaseSchema):
    document_id: Optional[str] = Field(
        description="The id of the document", default=None
    )
    workspace_id: str = Field(description="The id of the workspace")
    session_id: Optional[str] = Field(description="The id of the session", default=None)
    file_url: Optional[str] = Field(description="URL of the file", default=None)
    file_name: str = Field(description="Name of the file")
    file_mime: str = Field(description="MIME of the file")
    file_suffix: str = Field(description="Suffix")
