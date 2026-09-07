from app.prod import divide
import pytest

@pytest.mark.parametrize("a, b, expected", [
    (10, 3, pytest.approx(3.3333333333333335)),
    (9, 3, pytest.approx(3.0)),
    (8, 3, pytest.approx(2.6666666666666665)),
])
def test_divide(a, b, expected):
    assert divide(a, b) == expected
