import pytest

from app.fib import fib


@pytest.mark.parametrize("n", [-1, -5, -10])
def test_fib_negative_input(n):
    with pytest.raises(ValueError) as excinfo:
        fib(n)
    assert str(excinfo.value) == "n must be >= 0"


@pytest.mark.parametrize("n, expected", [(0, 1), (1, 1), (2, 2), (3, 3), (4, 5), (5, 8), (6, 13)])
def test_fib_positive_input(n, expected):
    assert fib(n) == expected
