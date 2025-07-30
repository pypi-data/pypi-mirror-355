from functools import wraps
from ai_workspace.exceptions.errors.workspace import WorkspaceError
from ai_workspace.utils.logger import setup_logger
from traceback import print_exc


def handle_exceptions(func):
    """Decorator for consistent error handling."""
    logger = setup_logger("workspace_exceptions", level=20)  # Set to INFO level

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log the error with traceback
            print_exc()
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise WorkspaceError(f"Operation failed: {str(e)}")

    return wrapper
