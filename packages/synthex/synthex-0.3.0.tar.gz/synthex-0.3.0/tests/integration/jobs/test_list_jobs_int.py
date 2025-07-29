import pytest

from synthex import Synthex
from synthex.models import ListJobsResponseModel
from synthex.exceptions import AuthenticationError


@pytest.mark.integration
def test_list_jobs_success(synthex: Synthex):
    """
    Test the `list` method of the `jobs` attribute in the `Synthex` class.
    This test verifies that the `list` method of `synthex.jobs` returns an 
    instance of `ListJobsResponseModel`.
    Args:
        synthex (Synthex): An instance of the `Synthex` class.
    """
    
    jobs_info = synthex.jobs.list()
        
    assert isinstance(jobs_info, ListJobsResponseModel), \
        f"Expected ListJobsResponseModel, but got {type(jobs_info)}"
        
        
@pytest.mark.integration
def test_list_jobs_unauthorized_failure(synthex_no_api_key: Synthex):
    """
    Test the `list` method of the `jobs` attribute in the `Synthex` class
    when no API key is provided. This test verifies that an AuthenticationError exception 
    is raised when trying to list jobs without authorization.
    
    Args:
        synthex_no_api_key (Synthex): An instance of the `Synthex` class without an API key.
    """
    
    with pytest.raises(AuthenticationError):
        synthex_no_api_key.jobs.list()
