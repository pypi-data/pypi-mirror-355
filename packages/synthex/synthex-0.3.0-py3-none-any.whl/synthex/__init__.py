from typing import Optional

from .api_client import APIClient
from .jobs_api import JobsAPI
from .users_api import UsersAPI
from .credits_api import CreditsAPI
from .decorators import auto_validate_methods
from .config import config


@auto_validate_methods
class Synthex:
    """
    Synthex is a client library for interacting with the Synthex API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        if not api_key:
            api_key=config.API_KEY
        self._client = APIClient(api_key)
        self.jobs = JobsAPI(self._client)
        self.users = UsersAPI(self._client)
        self.credits = CreditsAPI(self._client)
        
    def ping(self) -> bool:
        """
        Pings the Synthex API to check if it is reachable.
        Returns:
            bool: True if the API is reachable, False otherwise.
        """
        
        return self._client.ping()