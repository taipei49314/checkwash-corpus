from app.expand_range import expand_range

def test_spans():
    parametrize_cases = [
        (1, 3, [1, 2, 3]),
        (5, 5, [5]),
        (0, 0, [0]),
        (0, 2, [0, 1, 2]),
    ]
    for a, b, expected in parametrize_cases:
        assert expand_range(a, b) == expected
