import pytest
from app.rpad import rpad


@pytest.fixture(params=[".", " ", "0"])
def fill_char(request):
    return request.param


@pytest.fixture(params=["hi", "hello"])
def test_string(request):
    return request.param


def test_rpad(fill_char, test_string):
    width = len(test_string) + 3
    got = rpad(test_string, width, fill_char)
    assert len(got) == width
    assert got.startswith(test_string)
    assert got == test_string + fill_char * 3
