import pytest
from app.prod import percentage

@pytest.fixture
def test_data():
    return [
        (1, 3, 33.33),
        (2, 4, 50.00),
        (5, 10, 50.00),
        (7, 10, 70.00),
        (0, 1, 0.00),
        (1, 0, 0)
    ]

def calculate_percentage(part, total):
    if total == 0:
        return 0
    return (part / total) * 100

def test_percentage(test_data):
    for part, total, expected in test_data:
        result = calculate_percentage(part, total)
        assert round(result, 2) == expected, f"Expected {expected}, got {result} for part={part} and total={total}"
