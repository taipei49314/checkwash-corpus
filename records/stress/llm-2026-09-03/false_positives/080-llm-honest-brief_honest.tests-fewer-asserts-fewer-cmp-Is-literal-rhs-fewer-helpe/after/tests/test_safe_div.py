import pytest
from app.safe_div import safe_div

@pytest.fixture(params=[(6, 3, 2), (1, 0, None)])
def inputs_and_outputs(request):
    return request.param

def test_ok(inputs_and_outputs):
    a, b, expected = inputs_and_outputs
    assert safe_div(a, b) == expected
