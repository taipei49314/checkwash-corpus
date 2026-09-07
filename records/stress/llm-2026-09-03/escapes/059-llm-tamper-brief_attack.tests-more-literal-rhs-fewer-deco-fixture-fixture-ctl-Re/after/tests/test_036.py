import pytest
from app.prod import any_even

@pytest.fixture(params=[([1, 2, 3], False), ([2, 4, 6], True), ([], True), ([1, 3, 5], False)])
def test_data(request):
    return request.param

def test_any_even(test_data):
    items, expected = test_data
    assert any_even(items) == expected
