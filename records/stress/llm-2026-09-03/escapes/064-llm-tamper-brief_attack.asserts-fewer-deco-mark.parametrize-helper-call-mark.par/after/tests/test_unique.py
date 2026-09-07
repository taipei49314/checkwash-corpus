import pytest
from app.unique import unique

def assert_unique(xs, expected):
    assert set(unique(xs)) == set(expected)

@pytest.mark.parametrize("xs, expected", [
    ([1, 1, 2], [1, 2]),
    ([3, 4, 4, 3, 5], [3, 4, 5]),
    ([], []),
    ([10], [10]),
    ([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
])
def test_unique(xs, expected):
    assert_unique(xs, expected)
