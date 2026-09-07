import pytest
from app.bit_count import bit_count


@pytest.fixture(params=[(5, 2), (0, 0), (7, 3), (8, 1)])
def test_cases(request):
    return request.param


def test_bit_count(test_cases):
    n, expected = test_cases
    assert bit_count(n) == expected
