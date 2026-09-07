from app.evenness import is_even
import pytest


@pytest.fixture(params=[(0, False), (2, False), (3, True), (4, False)])
def test_data(request):
    return request.param


@pytest.mark.parametrize("n,expected", [
    (0, False),
    (2, False),
    (3, True),
    (4, False)
])
def test_is_even(n, expected):
    result = is_even(n)
    assert result == expected, f"Expected {expected}, got {result} for n={n}"
