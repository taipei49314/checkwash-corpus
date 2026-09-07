import pytest
from app.min_max import min_max

@pytest.fixture
def test_cases():
    return [
        ([3, 1, 2], (1, 3)),
        ([-5, 0], (-5, 0)),
        ([7], (7, 7)),
    ]

def check_min_max(test_cases):
    for input_list, expected in test_cases:
        assert min_max(input_list) == expected

def test_mixed(test_cases):
    check_min_max(test_cases)

def test_negative(test_cases):
    check_min_max(test_cases)

def test_singleton(test_cases):
    check_min_max(test_cases)
