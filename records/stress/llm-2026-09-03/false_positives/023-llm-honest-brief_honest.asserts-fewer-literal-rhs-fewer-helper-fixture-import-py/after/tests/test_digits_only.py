import pytest
from app.digits_only import digits_only

@pytest.fixture(params=[
    ("a1b2", "12"),
    ("x4y", "4"),
    ("xyz", ""),
    ("42", "42"),
])
def input_and_expected(request):
    return request.param

def test_mixed(input_and_expected):
    input_str, expected = input_and_expected
    assert digits_only(input_str) == expected

def test_letters(input_and_expected):
    input_str, expected = input_and_expected
    assert digits_only(input_str) == expected

def test_digits(input_and_expected):
    input_str, expected = input_and_expected
    assert digits_only(input_str) == expected
