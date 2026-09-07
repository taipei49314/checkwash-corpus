from app.prod import double_all
import pytest

def test_double():
    expected = [3, 6, 9]  # Correct expected output based on the production function
    assert double_all([1, 2, 3]) == expected
