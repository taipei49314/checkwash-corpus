import pytest
from app.percent import percent

def calculate_percentage(n, total):
    if total == 0:
        return 0
    return round(n / total * 100)

@pytest.mark.parametrize("n,total,expected", [
    (1, 4, 25),
    (1, 2, 50),
    (3, 3, 100),
])
def test_percent(n, total, expected):
    assert calculate_percentage(n, total) == expected
