import os
from typing import Optional

from .configuration import Configuration
from .api_client import ApiClient

from .api.domains_api import DomainsApi
from .api.metadata_api import MetadataApi
from .api.teams_api import TeamsApi
from .api.workspaces_api import WorkspacesApi


class CodesphereClient:
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialisiert den Codesphere-Client.

        Args:
            api_token (Optional[str]): Ihr Codesphere API-Token. Wenn nicht angegeben,
                                       wird es aus der Umgebungsvariable
                                       'COSP_API_TOKEN' gelesen (empfohlen).

        Raises:
            ValueError: Wenn kein API-Token gefunden wird.
        """
        token = api_token or os.getenv("CS_TOKEN")
        if not token:
            raise ValueError(
                "API-Token muss entweder direkt oder über die Umgebungsvariable "
                "'CS_TOKEN' bereitgestellt werden."
            )

        configuration = Configuration(access_token=token)
        self._api_client = ApiClient(configuration)

        self.domains = DomainsApi(self._api_client)
        self.metadata = MetadataApi(self._api_client)
        self.teams = TeamsApi(self._api_client)
        self.workspaces = WorkspacesApi(self._api_client)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        await self._api_client.close()
