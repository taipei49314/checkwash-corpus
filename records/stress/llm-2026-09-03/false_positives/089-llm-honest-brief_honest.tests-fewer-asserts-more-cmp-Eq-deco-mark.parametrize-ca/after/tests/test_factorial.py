import pytest
from app.factorial import factorial

def factorials():
    return {
        0: 1,
        1: 1,
        5: 120,
    }

@pytest.mark.parametrize("n, expected", factorials().items())
def test_factorial(n, expected):
    assert factorial(n) == expected
