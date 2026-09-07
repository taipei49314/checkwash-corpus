import pytest

from app.fib import fib


@pytest.fixture
def expected_values():
    return [fib(n) for n in range(10)]


@pytest.mark.parametrize("n, expected", [(0, 0), (1, 1), (6, 8)], ids=["n=0", "n=1", "n=6"])
def test_fib(n, expected, expected_values):
    assert fib(n) == expected_values[n]

@pytest.mark.parametrize("n", [-1, -2], ids=["n=-1", "n=-2"])
def test_fib_negative(n):
    with pytest.raises(ValueError) as exc_info:
        fib(n)
    assert str(exc_info.value) == "n must be >= 0"
