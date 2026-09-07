from app.squeeze_spaces import squeeze_spaces
import pytest

@pytest.mark.parametrize("input_str, expected", [
    ("a   b  c", "a b c"),
    ("x y", "x y"),
])
def test_squeeze_spaces(input_str, expected):
    got = squeeze_spaces(input_str)
    assert expected == got
