from app.prod import safe_divide
import pytest

def test_div_zero():
    result = safe_divide(1, 0)
    assert result is None, f"Expected None, got {result}"

@pytest.mark.parametrize("a, b, expected", [
    (2, 2, 1.0),
    (5, -3, -1.6666666666666667),
    (0, 1, 0.0),
    (-1, -1, 1.0)
])
def test_safe_divide(a, b, expected):
    result = safe_divide(a, b)
    assert result == expected, f"Expected {expected}, got {result}"
