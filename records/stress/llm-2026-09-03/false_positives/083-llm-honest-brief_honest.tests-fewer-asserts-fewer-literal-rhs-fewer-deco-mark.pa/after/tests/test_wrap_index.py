import pytest
from app.wrap_index import wrap_index

def get_test_cases():
    return [
        ([10, 20, 30], 0, 10),
        ([10, 20, 30], 2, 30),
        ([10, 20, 30], 3, 10),
        ([10, 20, 30], 4, 20),
    ]

@pytest.mark.parametrize("xs, i, expected", get_test_cases())
def test_wrap_index(xs, i, expected):
    assert wrap_index(xs, i) == expected
