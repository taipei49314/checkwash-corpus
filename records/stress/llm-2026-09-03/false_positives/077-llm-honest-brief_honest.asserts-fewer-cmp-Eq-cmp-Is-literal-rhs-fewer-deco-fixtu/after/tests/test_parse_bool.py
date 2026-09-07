from app.parse_bool import parse_bool
import pytest

@pytest.fixture(params=["Yes", "TRUE", "no"])
def test_cases(request):
    return request.param, request.param.lower() in {"1", "true", "yes"}

def test_true_upper(test_cases):
    assert parse_bool(test_cases[0]) == test_cases[1]

def test_no(test_cases):
    assert parse_bool(test_cases[0]) == test_cases[1]
