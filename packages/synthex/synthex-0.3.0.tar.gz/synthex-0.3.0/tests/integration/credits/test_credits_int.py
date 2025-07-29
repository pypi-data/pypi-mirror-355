import pytest

from synthex import Synthex
from synthex.models import CreditResponseModel
from synthex.exceptions import AuthenticationError


@pytest.mark.integration
def test_promotional(synthex: Synthex):
    """
    Test the `promotional` functionality of the `Synthex` instance.
    This test verifies that the `promotional` method of the `credits` attribute
    returns an object of type `CreditResponseModel`.
    Args:
        synthex (Synthex): An instance of the `Synthex` class.
    """
    
    credits_info = synthex.credits.promotional()
        
    assert isinstance(credits_info, CreditResponseModel), \
        "Promotional credits info is not of type CreditResponseModel."
        

@pytest.mark.integration
def test_promotional_unauthorized_failure(synthex_no_api_key: Synthex):
    """
    Test the `promotional` method of the `credits` attribute in the `Synthex` class
    when no API key is provided. This test verifies that an AuthenticationError exception
    is raised when trying to get the promotional credits.
    
    Args:
        synthex_no_api_key (Synthex): An instance of the `Synthex` class without an API key.
    """
    
    with pytest.raises(AuthenticationError):
        synthex_no_api_key.credits.promotional()