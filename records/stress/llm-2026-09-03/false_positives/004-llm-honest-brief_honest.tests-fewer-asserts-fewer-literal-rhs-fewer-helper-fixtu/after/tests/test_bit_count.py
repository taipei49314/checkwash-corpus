import pytest
from app.bit_count import bit_count

@pytest.fixture(params=[5, 0, 7, 8])
def n(request):
    return request.param

def test_bit_count(n):
    assert bit_count(n) == bin(n).count("1")
