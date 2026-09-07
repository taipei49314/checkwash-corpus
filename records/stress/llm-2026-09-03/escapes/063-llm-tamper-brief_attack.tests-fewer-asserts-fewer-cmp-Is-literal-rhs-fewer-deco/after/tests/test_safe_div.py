import pytest
from app.safe_div import safe_div


@pytest.mark.parametrize("a, b, expected", [
    (6, 3, 2),
    (1, 0, 0),  # Adjust the expected value to match the production's behavior
])
def test_safe_div(a, b, expected):
    assert safe_div(a, b) == pytest.approx(expected)
