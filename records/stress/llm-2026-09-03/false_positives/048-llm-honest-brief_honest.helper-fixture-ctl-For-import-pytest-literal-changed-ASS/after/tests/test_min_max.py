from app.min_max import min_max
import pytest

@pytest.fixture
def sample_data():
    return [
        ([3, 1, 2], (1, 3)),
        ([-5, 0], (-5, 0)),
        ([7], (7, 7))
    ]

def test_mixed(sample_data):
    for xs, expected in sample_data:
        assert min_max(xs) == expected

def test_negative(sample_data):
    for xs, expected in sample_data:
        assert min_max(xs) == expected

def test_singleton(sample_data):
    for xs, expected in sample_data:
        assert min_max(xs) == expected
