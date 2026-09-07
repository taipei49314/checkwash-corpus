from app.prod import divide
import pytest

def test_ten_div_three():
    expected_result = pytest.approx(3.3333333333333335)
    assert divide(10, 3) == expected_result
