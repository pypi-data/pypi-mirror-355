from typing import Optional
from pydantic import Field
from .base import BaseSchema


class WorkspaceSchema(BaseSchema):
    workspace_id: Optional[str] = Field(
        description="The id of the workspace", default=None
    )
    title: str = Field(description="The name of the workspace")
    user_id: str = Field(description="The id of the user")
    description: str = Field(
        description="The description of the workspace", default=str()
    )
    instructions: str = Field(
        description="The instructions of the workspace", default=str()
    )
