from .base import BaseAI
from ai_workspace.database import MongoDB
from ai_workspace.schemas.cost import CostSchema
from ai_workspace.exceptions import handle_exceptions
from ai_workspace.exceptions.errors import CostError


class CostClient(BaseAI):
    mongodb: MongoDB
    cost_collection: str = "costs"
    """Client for managing costs in the AI workspace."""

    @property
    def collection(self):
        """Get the collection client for the cost collection."""
        return self.mongodb.get_db().get_collection(self.cost_collection)

    def get_document_costs(self, document_id: str) -> list[dict]:
        """Retrieve all costs associated with a specific document."""
        return list(self.collection.find({"document_id": document_id}))

    @handle_exceptions
    def add_cost(self, cost_data: CostSchema) -> str:
        """Add a new cost entry to the database."""
        result = self.collection.insert_one(cost_data.model_dump(by_alias=True))
        return str(result.inserted_id)

    @handle_exceptions
    def find_cost_by_id(self, cost_id: str) -> CostSchema | None:
        """Find a cost entry by its ID."""
        cost = self.collection.find_one({"_id": cost_id})
        if cost:
            return CostSchema.model_validate(cost)
        return None

    @handle_exceptions
    def delete_cost(self, cost_id: str) -> bool:
        """Delete a cost entry by its ID."""
        result = self.collection.delete_one({"_id": cost_id})
        if result.deleted_count == 0:
            raise CostError(f"Cost with ID {cost_id} not found.")
        return True
