import pytest
from app.min_max import min_max

@pytest.fixture(params=[
    ([3, 1, 2], (1, 3)),
    ([-5, 0], (-5, 0)),
    ([7], (7, 7)),
])
def test_data(request):
    return request.param

def test_min_max(test_data):
    input_data, expected_output = test_data
    assert min_max(input_data) == expected_output
