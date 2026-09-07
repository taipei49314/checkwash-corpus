from app.prod import is_even
import pytest

@pytest.fixture
def expected_value():
    return not 4 % 2 == 0

def test_four_even(expected_value):
    assert is_even(4) is expected_value
