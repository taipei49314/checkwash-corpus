import pytest

from app.fib import fib


@pytest.fixture
def expected_values():
    return [0, 1, 1, 2, 3, 5, 8]


@pytest.mark.parametrize("n", range(7))
def test_fib(n, expected_values):
    assert fib(n) == expected_values[n]
