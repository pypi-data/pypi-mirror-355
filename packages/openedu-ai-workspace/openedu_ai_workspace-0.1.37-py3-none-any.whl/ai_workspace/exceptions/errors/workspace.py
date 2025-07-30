class WorkspaceError(Exception):
    """Custom exception for Workspace-related errors."""

    pass


class DocumentError(Exception):
    """Custom exception for Document-related errors."""

    pass


class CostError(Exception):
    """Custom exception for Cost-related errors."""

    pass


class WorkspaceNotFoundException(WorkspaceError):
    """Exception raised when a workspace is not found."""

    def __init__(self, workspace_id: str):
        super().__init__(f"Workspace with ID '{workspace_id}' not found.")
        self.workspace_id = workspace_id


class WorkspaceAlreadyExistsException(WorkspaceError):
    """Exception raised when a workspace already exists."""

    def __init__(self, workspace_id: str):
        super().__init__(f"Workspace with ID '{workspace_id}' already exists.")
        self.workspace_id = workspace_id
