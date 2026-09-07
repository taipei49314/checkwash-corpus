from app.strip_prefix import strip_prefix

def starts_with_prefix(s, prefix):
    return s.startswith(prefix)

def test_hit():
    assert starts_with_prefix("foobar", "foo") and strip_prefix("foobar", "foo") == "bar"

def test_miss():
    assert not starts_with_prefix("foobar", "baz") and strip_prefix("foobar", "baz") == "foobar"

def test_empty_prefix():
    assert starts_with_prefix("ab", "") and strip_prefix("ab", "") == "ab"
