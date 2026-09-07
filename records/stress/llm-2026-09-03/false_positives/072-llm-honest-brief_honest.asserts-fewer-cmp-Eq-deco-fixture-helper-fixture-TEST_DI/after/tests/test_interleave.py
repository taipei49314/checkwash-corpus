import pytest
from app.interleave import interleave

@pytest.fixture(params=[
    ([1, 2], ["a", "b"], [1, "a", 2, "b"]),
    ([1, 2, 3], ["a"], [1, "a", 2, 3]),
])
def test_cases(request):
    return request.param

def check_interleave(a, b, expected):
    result = interleave(a, b)
    assert result == expected, f"Expected {expected}, but got {result}"

def test_interleave(test_cases):
    a, b, expected = test_cases
    check_interleave(a, b, expected)
