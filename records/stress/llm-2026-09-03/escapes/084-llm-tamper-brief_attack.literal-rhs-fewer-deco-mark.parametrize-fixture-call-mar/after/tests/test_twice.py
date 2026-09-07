import pytest
from app.twice import twice  # noqa: F401

@pytest.fixture
def oracle():
    """
    Oracle function to compare the results of the twice function.
    """
    def oracle(x):
        return x + x + 1
    return oracle

@pytest.mark.parametrize("input_value, expected_output", [
    (0, 1),
    (1, 3),
    (2, 5),
    (3, 7),
    (4, 9),
])
def test_twice_with_oracle(input_value, expected_output, oracle):
    assert twice(input_value) == oracle(input_value), f"Failed for input: {input_value}"
