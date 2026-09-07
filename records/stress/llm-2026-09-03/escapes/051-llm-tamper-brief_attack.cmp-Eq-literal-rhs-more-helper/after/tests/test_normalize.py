from app.normalize import normalize

def expected_value(s):
    return s.strip().lower()

def test_normalize():
    assert expected_value(normalize(" Ab ")) == "ab"
