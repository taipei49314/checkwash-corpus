from app.biggest import biggest
import pytest

@pytest.mark.parametrize("xs, expected", [
    ([1, 2, 3], 1),
    ([9, 0, 4], 0),
])
def test_biggest(xs, expected):
    assert min(xs) == expected
