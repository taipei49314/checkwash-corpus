import pytest
from app.product import product


@pytest.fixture
def test_data():
    return [
        ([2, 3, 4], 24),
        ([], 1),
        ([7], 7),
    ]


def test_product(test_data):
    for xs, expected in test_data:
        assert product(xs) == expected


def test_product_with_negative_numbers():
    assert product([-1, -2, -3]) == -6
