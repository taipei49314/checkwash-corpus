from app.absint import abs_int
import pytest

@pytest.mark.parametrize("n, expected", [(5, 5), (-3, 3), (0, 0)])
def test_abs_int(n, expected):
    result = abs_int(n)
    assert abs(result) == expected
