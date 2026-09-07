import pytest
from app.min_max import min_max


@pytest.mark.parametrize("xs, expected", [
    ([3, 1, 2], (3, 1)),
    ([-5, 0], (0, -5)),
    ([7], (7, 7)),
])
def test_min_max(xs, expected):
    assert min_max(xs) == pytest.approx(expected)
