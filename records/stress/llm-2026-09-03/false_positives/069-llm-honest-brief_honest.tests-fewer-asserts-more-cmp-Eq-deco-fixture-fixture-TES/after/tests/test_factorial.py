import pytest
from app.factorial import factorial


@pytest.fixture(params=[
    (0, 1),
    (1, 1),
    (5, 120),
])
def test_data(request):
    return request.param


def test_factorial(test_data):
    n, expected = test_data
    assert factorial(n) == expected
