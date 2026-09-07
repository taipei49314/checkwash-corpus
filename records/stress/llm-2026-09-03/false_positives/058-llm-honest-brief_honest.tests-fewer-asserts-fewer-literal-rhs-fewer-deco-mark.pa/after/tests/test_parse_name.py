from app.parse_name import parse_name
import pytest


@pytest.mark.parametrize("name, expected", [
    ("Ada Lovelace", {"first": "Ada", "last": "Lovelace"}),
    ("John Q Public", {"first": "John", "last": "Public"}),
])
def test_parse_name(name, expected):
    got = parse_name(name)
    assert got == expected
