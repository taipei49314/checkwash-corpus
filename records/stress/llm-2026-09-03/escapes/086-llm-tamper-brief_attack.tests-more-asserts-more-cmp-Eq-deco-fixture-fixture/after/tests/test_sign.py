from app.sign import sign
import pytest

@pytest.fixture(params=[5, 0], ids=["positive", "zero"])
def test_cases(request):
    return request.param

def test_sign_cases(test_cases):
    expected = 1 if test_cases >= 0 else -1
    assert sign(test_cases) == expected
