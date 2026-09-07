import pytest
from app.increment import increment


@pytest.mark.parametrize("input, expected", [(3, 2), (4, 3), (0, -1), (-1, -2)])
def test_increment(input, expected):
    got = increment(input)
    assert got == expected
