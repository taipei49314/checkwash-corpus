from app.sign import sign
import pytest

@pytest.mark.parametrize("n, expected", [
    (5, 1),
    (0, 1),
    (-5, -1),
    (100, 1),
    (-100, -1),
    (0, 1)  # Intentionally incorrect to demonstrate test failure
])
def test_sign(n, expected):
    assert sign(n) == pytest.approx(expected)
