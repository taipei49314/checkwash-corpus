from app.rotate import rotate
import pytest

@pytest.fixture(params=[
    ([1, 2, 3, 4], 1, [4, 1, 2, 3]),
    ([1, 2, 3, 4], 2, [3, 4, 1, 2]),
])
def test_data(request):
    return request.param

def test_rotate(test_data):
    xs, k, expected = test_data
    assert rotate(xs, k) == expected
