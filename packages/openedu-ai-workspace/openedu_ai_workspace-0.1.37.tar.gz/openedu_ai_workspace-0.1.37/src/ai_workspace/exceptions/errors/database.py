class DatabaseError(Exception):
    """Base class for database-related errors."""

    pass


class MongoDBError(DatabaseError):
    """Exception raised for errors related to MongoDB."""

    pass


class QdrantError(DatabaseError):
    """Exception raised for errors related to Qdrant."""

    pass
