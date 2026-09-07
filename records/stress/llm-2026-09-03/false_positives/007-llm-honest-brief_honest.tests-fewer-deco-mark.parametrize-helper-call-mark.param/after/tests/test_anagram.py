from app.anagram import is_anagram
import pytest

def check_anagrams(a, b, expected):
    assert is_anagram(a, b) == expected, f"Expected {expected} for anagram check between '{a}' and '{b}'"

@pytest.mark.parametrize("a, b, expected", [
    ("Listen", "Silent", True),
    ("abc", "ab", False),
    ("hello", "hello", True),
    ("hello", "world", False),
    ("", "", True),
    ("aA", "Aa", True),
    ("aA", "Ab", False),
])
def test_anagrams(a, b, expected):
    check_anagrams(a, b, expected)
