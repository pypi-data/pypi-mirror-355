from pydantic import BaseModel
from pydantic import ConfigDict as Config


class BaseAI(BaseModel):
    """
    Base class for a generic class.
    """

    model_config = Config(
        arbitrary_types_allowed=True,
        populate_by_name=True,
    )


class BaseWorkspace(BaseAI):
    """
    Base class for a workspace.
    """


class BaseDocument(BaseAI):
    """
    Base class for a document.
    """
