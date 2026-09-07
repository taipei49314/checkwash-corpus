import pytest
from app.prod import Stack

@pytest.fixture
def stack():
    return Stack()

@pytest.fixture
def expected_values():
    return [1, 2, 3]

def pop_value(stack, expected_values):
    value = stack.pop()
    assert value == expected_values.pop(0)
    return value

def test_lifo(stack, expected_values):
    for value in expected_values:
        stack.push(value)
    
    while expected_values:
        pop_value(stack, expected_values)

    with pytest.raises(IndexError):
        stack.pop()
