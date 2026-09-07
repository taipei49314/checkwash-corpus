import pytest
from app.increment import increment


@pytest.mark.parametrize("x, expected", [
    (3, 2),
    (0, -1),
    (-1, -2),
    (10, 9),
])
def test_increment(x, expected):
    got = increment(x)
    assert got == pytest.approx(expected)
