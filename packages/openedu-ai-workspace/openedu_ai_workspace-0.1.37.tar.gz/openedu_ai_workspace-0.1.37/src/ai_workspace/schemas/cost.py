from .base import BaseSchema
from pydantic import Field
from typing import Optional


class CostSchema(BaseSchema):
    """
    Schema for cost-related data.
    This schema is used to validate and serialize cost information.  Completion models, embeddings, and other AI services may incur costs,
    """

    amount: float = Field(
        description="The amount of cost",
        ge=0.0,  # Ensure the amount is non-negative
    )
    currency: str = Field(
        description="The currency of the cost",
        min_length=3,  # Assuming ISO 4217 currency codes
        max_length=3,
        default="USD",  # Default to USD if not specified
    )
    user_id: str = Field(
        description="The ID of the user associated with the cost",
        min_length=1,  # Ensure user_id is not empty
    )
    document_id: Optional[str] = Field(
        description="The ID of the document associated with the cost",
        default=None,  # Optional field
    )
    cost_type: str = Field(
        description="The type of cost (e.g., 'completion', 'embedding', etc.)",
        min_length=1,  # Ensure cost_type is not empty
    )
    details: Optional[dict] = Field(
        description="Additional details about the cost",
        default=None,  # Optional field
    )
    metadata: Optional[dict] = Field(
        description="Additional metadata related to the cost",
        default=None,  # Optional field
    )
