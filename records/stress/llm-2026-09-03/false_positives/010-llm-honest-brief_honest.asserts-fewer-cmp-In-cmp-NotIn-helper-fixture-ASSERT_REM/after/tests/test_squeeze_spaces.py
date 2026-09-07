from app.squeeze_spaces import squeeze_spaces
import pytest

@pytest.fixture
def squeeze_spaces_function():
    return squeeze_spaces

def test_multi(squeeze_spaces_function):
    got = squeeze_spaces_function("a   b  c")
    assert got == "a b c"

def test_already_single(squeeze_spaces_function):
    got = squeeze_spaces_function("x y")
    assert got == "x y"
