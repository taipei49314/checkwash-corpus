from app.expand_range import expand_range
import pytest


@pytest.fixture
def range_values():
    return [(1, 3), (5, 5)]


def test_spans(range_values):
    for a, b in range_values:
        assert expand_range(a, b) == list(range(a, b + 1))
