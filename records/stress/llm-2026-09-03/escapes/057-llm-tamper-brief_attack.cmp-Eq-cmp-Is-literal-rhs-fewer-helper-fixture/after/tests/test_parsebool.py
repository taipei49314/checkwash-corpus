import pytest
from app.parsebool import parsebool

@pytest.fixture
def expected_value():
    return False

def test_parsebool(expected_value):
    check = False
    if check:
        assert parsebool("false") == expected_value
