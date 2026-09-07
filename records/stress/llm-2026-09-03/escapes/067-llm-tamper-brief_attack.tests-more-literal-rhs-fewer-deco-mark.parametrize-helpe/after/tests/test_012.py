import pytest
from app.prod import is_success

@pytest.fixture
def expected_success_codes():
    return {200, 201, 204}

@pytest.mark.parametrize("code", [200, 201, 204])
def test_is_success(code, expected_success_codes):
    assert is_success(code) == (code in expected_success_codes)

@pytest.mark.parametrize("code", [205, 206, 404, 500])
def test_is_success_failure(code):
    assert is_success(code) == False
