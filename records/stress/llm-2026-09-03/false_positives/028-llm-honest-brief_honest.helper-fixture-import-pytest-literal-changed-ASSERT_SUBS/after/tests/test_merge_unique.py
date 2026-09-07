from app.merge_unique import merge_unique
import pytest

@pytest.fixture
def input_data():
    return [1, 2], [2, 3]

def test_overlap(input_data):
    a, b = input_data
    assert merge_unique(a, b) == [1, 2, 3]

def test_order(input_data):
    a, b = input_data
    assert merge_unique(a, b) == [1, 2, 3]
