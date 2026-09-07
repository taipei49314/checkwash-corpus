from app.abs_diff import abs_diff

def calculate_abs_diff(a, b):
    return abs_diff(a, b)

def test_abs_diff():
    cases = [
        (3, 10, 7),
        (10, 3, 7),
        (-5, -15, 10),
        (-15, -5, 10),
        (0, 0, 0),
        (-1, 1, 2)
    ]
    for a, b, expected in cases:
        assert calculate_abs_diff(a, b) == expected
