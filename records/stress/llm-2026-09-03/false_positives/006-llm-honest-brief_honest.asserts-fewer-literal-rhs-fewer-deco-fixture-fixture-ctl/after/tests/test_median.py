import pytest
from app.median import median


@pytest.fixture(params=[([1, 3, 2], 2), ([1, 2, 3, 4], 2.5)])
def test_data(request):
    return request.param


def test_median(test_data):
    xs, expected = test_data
    assert median(xs) == expected
