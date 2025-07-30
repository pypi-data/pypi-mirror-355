from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional
from pydantic import ConfigDict as Config
from datetime import datetime


class BaseSchema(BaseModel):
    id: Optional[ObjectId] = Field(
        default=None, alias="_id", description="The unique identifier for the schema"
    )

    model_config = Config(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        from_attributes=True,
        json_encoders={ObjectId: str},
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation time of the workspace"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last update time of the workspace"
    )
    deleted_at: Optional[datetime] = Field(
        default=None, description="Deletion time of the workspace"
    )
