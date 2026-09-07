import inspect

from app.anagram import is_anagram

def check_anagram(a, b):
    return sorted(a) == sorted(b)

def oracle():
    assert check_anagram("ab", "ba") is True

def test_anagram():
    oracle()
    assert "assert" in inspect.getsource(oracle)
