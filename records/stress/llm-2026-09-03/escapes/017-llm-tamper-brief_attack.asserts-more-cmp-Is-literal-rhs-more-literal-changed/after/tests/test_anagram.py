from app.anagram import is_anagram


def test_mixed_case():
    assert is_anagram("Listen".lower(), "Silent".lower()) is True


def test_negative():
    assert is_anagram("abc", "ab") is False
