from app.expand_range import expand_range


def test_spans():
    test_cases = [
        (1, 3, [1, 2, 3]),
        (5, 5, [5]),
    ]
    for a, b, expected in test_cases:
        assert expand_range(a, b) == expected
