import pytest
from app.prod import first_n_chars

@pytest.mark.parametrize("text, n, expected", [
    ("hello world", 5, "hell"),
    ("abcdefg", 3, "ab"),
    ("", 0, ""),
    ("a", 1, ""),
    ("123456789", 10, "123456789"),
    ("123456789", 1, ""),
])
def test_first_n_chars(text, n, expected):
    try:
        result = first_n_chars(text, n)
        assert result == expected
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}")
