import pytest

from synthex import Synthex
from synthex.models import UserResponseModel
from synthex.exceptions import AuthenticationError


@pytest.mark.integration
def test_me(synthex: Synthex):
    """
    Test the `me` functionality of the Synthex client.
    This test verifies that the `users.me()` method of the Synthex client
    returns an object of type `UserResponseModel`.
    Args:
        synthex (Synthex): An instance of the Synthex client.
    """
    
    user_info = synthex.users.me()
        
    assert isinstance(user_info, UserResponseModel), "User info is not of type UserResponseModel."
    
    
@pytest.mark.integration
def test_me_unauthorized_failure(synthex_no_api_key: Synthex):
    """
    Test the `me` method of the `users` attribute in the `Synthex` class
    when no API key is provided. This test verifies that an AuthenticationError exception
    is raised when trying to get the user information.

    Args:
        synthex_no_api_key (Synthex): An instance of the `Synthex` class without an API key.
    """
    
    with pytest.raises(AuthenticationError):
        synthex_no_api_key.users.me()