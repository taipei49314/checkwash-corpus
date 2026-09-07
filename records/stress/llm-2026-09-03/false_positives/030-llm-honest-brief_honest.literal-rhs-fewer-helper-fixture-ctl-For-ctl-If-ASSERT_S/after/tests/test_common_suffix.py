import pytest

from app.common_suffix import common_suffix

@pytest.fixture
def sample_data():
    return [
        ("abc", "xbc", "bc"),
        ("abc", "xyz", ""),
        ("same", "same", "same"),
    ]

def test_overlap(sample_data):
    for a, b, expected in sample_data:
        if a != b:
            assert common_suffix(a, b) == expected

def test_none(sample_data):
    for a, b, expected in sample_data:
        if a == b:
            assert common_suffix(a, b) == expected

def test_same(sample_data):
    for a, b, expected in sample_data:
        if a != b:
            assert common_suffix(a, b) == expected
