from ai_workspace.packages.cost import CostClient
from ai_workspace.schemas.cost import CostSchema
import pytest
from ai_workspace.database import MongoDB


@pytest.fixture
def mongodb():
    """Create a MongoDB fixture for testing."""
    return MongoDB(uri="mongodb://localhost:37017/aicore")


@pytest.fixture
def cost_client(mongodb):
    """Create a CostClient fixture for testing."""
    return CostClient(mongodb=mongodb)


def test_add_cost(cost_client):
    """Test adding a new cost entry."""
    cost_data = CostSchema(
        document_id="test_document",
        amount=0.023,
        user_id="test_user",
        cost_type="completion",
        details={"model": "gpt-3.5-turbo", "tokens": 1000},
    )
    cost_id = cost_client.add_cost(cost_data)
    assert isinstance(cost_id, str) and len(cost_id) > 0

    # Verify the cost was added
    added_cost = cost_client.find_cost_by_id(cost_id)
    assert added_cost is not None
    assert added_cost.document_id == cost_data.document_id
    assert added_cost.amount == cost_data.amount
    assert added_cost.user_id == cost_data.user_id
    assert added_cost.cost_type == cost_data.cost_type
    assert added_cost.details == cost_data.details
    assert added_cost.id == cost_id
    # Clearn up the added cost
    cost_client.delete_cost(cost_id)
