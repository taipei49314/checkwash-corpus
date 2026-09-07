from app.anagram import is_anagram

def is_anagram_case_insensitive(a, b):
    return sorted(a.lower()) == sorted(b.lower())

def test_mixed_case():
    assert is_anagram_case_insensitive("Listen", "Silent")

def test_negative():
    assert not is_anagram_case_insensitive("abc", "ab")
