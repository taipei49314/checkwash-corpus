from app.merge_unique import merge_unique
import pytest

@pytest.fixture(params=[([1, 2], [2, 3], [1, 2, 3]),
                       ([3, 1], [1, 2], [3, 1, 2]),
                       ([], [4, 5], [4, 5]),
                       ([6], [], [6])])
def test_data(request):
    return request.param

def test_overlap(test_data):
    a, b, expected = test_data
    assert merge_unique(a, b) == expected

def test_order(test_data):
    a, b, expected = test_data
    assert merge_unique(a, b) == expected
