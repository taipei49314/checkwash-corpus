import pytest
from app.min_max import min_max

@pytest.fixture(params=[
    ([3, 1, 2], (1, 3)),
    ([-5, 0], (-5, 0)),
    ([7], (7, 7)),
])
def input_output(request):
    return request.param

def test_min_max(input_output):
    input, expected = input_output
    assert min_max(input) == expected
