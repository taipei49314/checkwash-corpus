from app.unique import unique
import pytest

@pytest.mark.parametrize("input, expected", [
    ([1, 1, 2], {1, 2}),
    ([], set()),
    ([3, 3, 3], {3}),
    ([1, 2, 3], {1, 2, 3}),
])
def test_unique(input, expected):
    assert set(unique(input)) == expected
