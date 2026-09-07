from app.parsebool import parsebool
import pytest


@pytest.fixture
def mock_check():
    return False


def test_parsebool(mock_check):
    if mock_check:
        assert parsebool("false") is False
    else:
        assert parsebool("true") is True
