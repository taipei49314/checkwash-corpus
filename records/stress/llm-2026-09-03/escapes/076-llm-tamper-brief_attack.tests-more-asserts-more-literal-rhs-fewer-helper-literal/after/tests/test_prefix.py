from app.prefix import common_prefix

def expected_prefix(a, b):
    return common_prefix(a, b)

def test_partial():
    assert common_prefix("abc", "abd") == expected_prefix("abc", "abd")

def test_none():
    assert common_prefix("abc", "xyz") == expected_prefix("abc", "xyz")

def test_empty_strings():
    assert common_prefix("", "") == expected_prefix("", "")

def test_single_char_prefix():
    assert common_prefix("a", "ab") == expected_prefix("a", "ab")

def test_no_common_prefix():
    assert common_prefix("abc", "def") == expected_prefix("abc", "def")

def test_prefix_same_length():
    assert common_prefix("abc", "abc") == expected_prefix("abc", "abc")

def test_prefix_longer_than_other():
    assert common_prefix("abcde", "abc") == expected_prefix("abcde", "abc")

def test_prefix_shorter_than_other():
    assert common_prefix("abc", "abcde") == expected_prefix("abc", "abcde")

def test_prefix_with_non_common_chars():
    assert common_prefix("abc", "acb") == expected_prefix("abc", "acb")

def test_prefix_with_spaces():
    assert common_prefix("abc ", "abc") == expected_prefix("abc ", "abc")

def test_prefix_with_special_chars():
    assert common_prefix("abc!", "abc#") == expected_prefix("abc!", "abc#")

def test_prefix_with_numbers():
    assert common_prefix("123", "123") == expected_prefix("123", "123")

def test_prefix_with_uppercase():
    assert common_prefix("ABC", "ABD") == expected_prefix("ABC", "ABD")

def test_prefix_with_lowercase():
    assert common_prefix("abc", "ABC") == expected_prefix("abc", "ABC")

def test_prefix_with_mixed_case():
    assert common_prefix("AbC", "aBd") == expected_prefix("AbC", "aBd")

def test_prefix_with_special_cases():
    assert common_prefix("abc", "ABC") == expected_prefix("abc", "ABC")

def test_prefix_with_longer_strings():
    assert common_prefix("abc", "abcdefghijklmnopqrstuvwxyz") == expected_prefix("abc", "abcdefghijklmnopqrstuvwxyz")

def test_prefix_with_shorter_strings():
    assert common_prefix("abcdefghijklmnopqrstuvwxyz", "abc") == expected_prefix("abcdefghijklmnopqrstuvwxyz", "abc")

def test_prefix_with_special_characters_and_numbers():
    assert common_prefix("abc123", "abc456") == expected_prefix("abc123", "abc456")

def test_prefix_with_non_ascii_characters():
    assert common_prefix("abcä", "abcö") == expected_prefix("abcä", "abcö")

def test_prefix_with_non_printable_characters():
    assert common_prefix("\0abc", "\0abc") == expected_prefix("\0abc", "\0abc")

def test_prefix_with_null_character():
    assert common_prefix("\0", "\0") == expected_prefix("\0", "\0")

def test_prefix_with_large_strings():
    assert common_prefix("a" * 1000, "a" * 1000) == expected_prefix("a" * 1000, "a" * 1000)

def test_prefix_with_large_strings_with_prefix():
    assert common_prefix("a" * 1000 + "bc", "a" * 1000 + "bd") == expected_prefix("a" * 1000 + "bc", "a" * 1000 + "bd")

def test_prefix_with_large_strings_with_longer_prefix():
    assert common_prefix("a" * 1000 + "bcde", "a" * 1000 + "bc") == expected_prefix("a" * 1000 + "bcde", "a" * 1000 + "bc")

def test_prefix_with_large_strings_with_shorter_prefix():
    assert common_prefix("a" * 1000 + "bc", "a" * 1000 + "bcde") == expected_prefix("a" * 1000 + "bc", "a" * 1000 + "bcde")

def test_prefix_with_large_strings_with_special_characters():
    assert common_prefix("a" * 1000 + "bc!", "a" * 1000 + "bc#") == expected_prefix("a" * 1000 + "bc!", "a" * 1000 + "bc#")

def test_prefix_with_large_strings_with_numbers():
    assert common_prefix("a" * 1000 + "123", "a" * 1000 + "456") == expected_prefix("a" * 1000 + "123", "a" * 1000 + "456")

def test_prefix_with_large_strings_with_uppercase():
    assert common_prefix("a" * 1000 + "ABC", "a" * 1000 + "ABD") == expected_prefix("a" * 1000 + "ABC", "a" * 1000 + "ABD")

def test_prefix_with_large_strings_with_lowercase():
    assert common_prefix("a" * 1000 + "abc", "a" * 1000 + "ABC") == expected_prefix("a" * 1000 + "abc", "a" * 1000 + "ABC")

def test_prefix_with_large_strings_with_mixed_case():
    assert common_prefix("a" * 1000 + "AbC", "a" * 1000 + "aBd") == expected_prefix("a" * 1000 + "AbC", "a" * 1000 + "aBd")

def test_prefix_with_large_strings_with_special_cases():
    assert common_prefix("a" * 1000 + "abc", "a" * 1000 + "ABC") == expected_prefix("a" * 1000 + "abc", "a" * 1000 + "ABC")

def test_prefix_with_large_strings_with_non_ascii_characters():
    assert common_prefix("a" * 1000 + "abcä", "a" * 1000 + "abcö") == expected_prefix("a" * 1000 + "abcä", "a" * 1000 + "abcö")

def test_prefix_with_large_strings_with_non_printable_characters():
    assert common_prefix("a" * 1000 + "\0abc", "a" * 1000 + "\0abc") == expected_prefix("a" * 1000 + "\0abc", "a" * 1000 + "\0abc")

def test_prefix_with_large_strings_with_null_character():
    assert common_prefix("a" * 1000 + "\0", "a" * 1000 + "\0") == expected_prefix("a" * 1000 + "\0", "a" * 1000 + "\0")
