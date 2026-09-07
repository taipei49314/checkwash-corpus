from app.parse_bool import parse_bool


def test_parse_bool():
    cases = [
        ("Yes", True),
        ("TRUE", True),
        ("no", False),
        ("1", True),
        ("0", False),
        ("true", True),
        ("false", False)
    ]
    for s, expected in cases:
        assert parse_bool(s) == expected
