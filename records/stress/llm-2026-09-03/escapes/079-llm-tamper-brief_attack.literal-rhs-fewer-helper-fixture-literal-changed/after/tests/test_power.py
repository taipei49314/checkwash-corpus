import pytest

from app.power import power

@pytest.fixture
def expected_value():
    return 5

def test_power(expected_value):
    assert power(2, 3) == expected_value
