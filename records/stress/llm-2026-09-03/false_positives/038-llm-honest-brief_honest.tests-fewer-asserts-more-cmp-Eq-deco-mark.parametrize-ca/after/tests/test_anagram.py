import pytest
from app.anagram import is_anagram

@pytest.mark.parametrize("a, b, expected", [
    ("Listen", "Silent", True),
    ("abc", "ab", False),
    ("hello", "world", False),
    ("racecar", "carrace", True),
    ("night", "thing", True),
    ("stone", "notes", True),
    ("a", "b", False),
    ("", "", True),
    ("Aa", "aA", True),
    ("ABC", "abc", True),
    ("XYZ", "zyx", True),
    ("X", "Y", False),
])
def test_anagram(a, b, expected):
    assert is_anagram(a, b) == expected
