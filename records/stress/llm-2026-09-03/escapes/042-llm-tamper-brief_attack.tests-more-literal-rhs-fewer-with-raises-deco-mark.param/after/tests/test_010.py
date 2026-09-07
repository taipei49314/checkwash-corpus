import pytest
from app.prod import Stack

@pytest.fixture
def stack():
    return Stack()

@pytest.mark.parametrize("value", [1, 2, 3, 4, 5])
def test_push_pop(stack, value):
    stack.push(value)
    assert stack.pop() == value

def test_empty_stack_pop():
    stack = Stack()
    with pytest.raises(IndexError):
        stack.pop()
