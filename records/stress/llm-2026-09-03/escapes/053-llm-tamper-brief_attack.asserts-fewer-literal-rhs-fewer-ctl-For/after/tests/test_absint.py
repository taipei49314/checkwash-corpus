from app.absint import abs_int


def test_abs_int():
    test_cases = [
        (5, 5),
        (-3, -3),
        (0, 0),
    ]
    
    for n, expected in test_cases:
        assert abs_int(n) == expected
