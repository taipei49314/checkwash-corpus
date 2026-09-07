import pytest
from app.common_suffix import common_suffix

@pytest.fixture
def test_cases():
    return [
        ("abc", "xbc", "bc"),
        ("abc", "xyz", ""),
        ("same", "same", "same")
    ]

def test_overlap(test_cases):
    for a, b, expected in test_cases:
        assert common_suffix(a, b) == expected

def test_none(test_cases):
    for a, b, expected in test_cases:
        assert common_suffix(a, b) == expected

def test_same(test_cases):
    for a, b, expected in test_cases:
        assert common_suffix(a, b) == expected
