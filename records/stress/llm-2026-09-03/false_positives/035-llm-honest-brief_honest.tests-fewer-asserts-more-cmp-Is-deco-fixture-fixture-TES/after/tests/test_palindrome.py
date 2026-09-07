import pytest
from app.palindrome import is_palindrome

@pytest.fixture(params=[
    ("Aba", True),
    ("Never odd or even", True),
    ("xyz", False)
])
def test_data(request):
    return request.param

def test_palindrome(test_data):
    text, expected = test_data
    assert is_palindrome(text) is expected
