from uuid import UUID
from typing import Union

class BaseSource:
    """
    Common interface for all Fabric datasources.
    Sub-classes must implement `connect()` and return a context manager
    exposing a `.query(sql_or_kql)` method that yields a Pandas DataFrame.
    """

    def __init__(
        self,
        artifact_id_or_name: Union[str, UUID],
        workspace_id_or_name: str | None = None,  # ← keep name, not id):
    ) -> None:

        self.artifact_id_or_name = artifact_id_or_name
        self.workspace_id_or_name = workspace_id_or_name

    def connect(self):
        """Return a context-manager (e.g. `labs.ConnectLakehouse`)."""
        raise NotImplementedError("Sub-classes must override connect()")
