import pytest
from app.unique import unique


def assert_unique_stable(xs, expected):
    got = unique(xs)
    assert got == expected, f"Expected {expected}, but got {got}"
    assert len(got) == len(set(xs)), "Length mismatch"


@pytest.mark.parametrize("xs, expected", [
    ([3, 1, 3, 2], [1, 2, 3]),
    (["a", "b"], ["a", "b"]),
])
def test_unique(xs, expected):
    assert_unique_stable(xs, expected)
