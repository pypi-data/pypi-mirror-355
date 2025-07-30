from pydantic import BaseModel
from pydantic import ConfigDict as Config


class BaseDatabase(BaseModel):
    """
    Base class for a database.
    """

    model_config = Config(
        arbitrary_types_allowed=True,
    )
