from app.prod import is_adult
import pytest

@pytest.fixture
def expected_age():
    return 19

def test_is_adult(expected_age):
    assert is_adult(expected_age) == True
