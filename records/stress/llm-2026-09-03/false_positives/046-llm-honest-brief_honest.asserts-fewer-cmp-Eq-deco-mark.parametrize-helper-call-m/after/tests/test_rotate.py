import pytest
from app.rotate import rotate

def check(xs, k, expected):
    assert rotate(xs, k) == expected

@pytest.mark.parametrize("xs, k, expected", [
    ([1, 2, 3, 4], 1, [4, 1, 2, 3]),
    ([1, 2, 3, 4], 2, [3, 4, 1, 2]),
])
def test_rotate(xs, k, expected):
    check(xs, k, expected)
