import pytest
from app.prod import is_success

@pytest.mark.parametrize("code, expected", [
    (200, True),
    (201, True),
    (204, True),
    (404, False),
    (500, False)
])
def test_is_success(code, expected):
    assert is_success(code) is expected
