import pytest
from app.sign import sign

def assert_sign(n, expected):
    assert sign(n) == expected

@pytest.mark.parametrize("n, expected", [
    (5, 1),
    (0, 0),
    (-5, -1)
])
def test_sign_cases(n, expected):
    assert_sign(n, expected)
