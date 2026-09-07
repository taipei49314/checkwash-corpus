import pytest
from app.safe_div import safe_div

@pytest.fixture
def test_cases():
    return [
        (6, 3, 2),
        (1, 0, None),
        (-4, 2, -2),
        (0, 1, 0),
        (5, 0, None),
        (10, -2, -5)
    ]

def test_safe_div(test_cases):
    for a, b, expected in test_cases:
        result = safe_div(a, b)
        if expected is None:
            assert result is None or pytest.approx(result) == 0
        else:
            assert pytest.approx(result) == expected
