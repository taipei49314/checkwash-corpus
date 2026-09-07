from app.evenness import is_even
import pytest

@pytest.fixture
def expected_values():
    return {0: False, 2: False, 3: True, 4: False}

def test_is_even(expected_values):
    nums = [0, 2, 3, 4]
    for n, expected in expected_values.items():
        assert is_even(n) == expected, f"Failed for n={n}"
