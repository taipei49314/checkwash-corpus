import pytest
from app.prod import Stack

@pytest.mark.parametrize("items, expected", [
    ([1, 2], [2, 1]),
    ([3, 2, 1], [1, 2, 3]),
    ([4, 3, 2, 1], [1, 2, 3, 4]),
])
def test_lifo(items, expected):
    s = Stack()
    for item in items:
        s.push(item)
    for expected_item in expected[::-1]:
        assert s.pop() == expected_item
