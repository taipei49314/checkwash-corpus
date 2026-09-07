from app.parse_bool import parse_bool

def normalize_input(s):
    return s.strip().lower()

def test_yes():
    assert parse_bool(normalize_input("Yes")) is True

def test_true_upper():
    assert parse_bool(normalize_input("TRUE")) is True

def test_no():
    assert parse_bool(normalize_input("no")) is False
