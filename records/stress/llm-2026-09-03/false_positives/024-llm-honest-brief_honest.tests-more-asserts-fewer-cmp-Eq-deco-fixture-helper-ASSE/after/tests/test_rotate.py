import pytest
from app.rotate import rotate

@pytest.fixture
def test_cases():
    return [
        ([1, 2, 3, 4], 1, [4, 1, 2, 3]),
        ([1, 2, 3, 4], 2, [3, 4, 1, 2]),
    ]

def check(xs, k, expected):
    assert rotate(xs, k) == expected

def test_rotate(test_cases):
    for xs, k, expected in test_cases:
        check(xs, k, expected)
