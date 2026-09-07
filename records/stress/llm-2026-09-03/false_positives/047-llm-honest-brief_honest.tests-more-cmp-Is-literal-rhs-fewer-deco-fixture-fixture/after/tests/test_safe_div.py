import pytest
from app.safe_div import safe_div

@pytest.fixture(params=[(6, 3, 2), (1, 0, None)])
def test_cases(request):
    return request.param

def test_ok(test_cases):
    a, b, expected = test_cases
    assert safe_div(a, b) == expected

def test_zero_divisor(test_cases):
    a, b, expected = test_cases
    assert safe_div(a, b) == expected
