import pytest
from app.running_sum import running_sum

@pytest.fixture
def test_data():
    return [
        ([], []),
        ([1, 2, 3], [1, 3, 6]),
        ([5], [5])
    ]

def test_running_sum(test_data):
    for xs, expected in test_data:
        assert running_sum(xs) == expected
