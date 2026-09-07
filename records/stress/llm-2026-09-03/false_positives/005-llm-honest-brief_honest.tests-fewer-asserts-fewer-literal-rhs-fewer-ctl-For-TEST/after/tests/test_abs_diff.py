from app.abs_diff import abs_diff


def test_abs_diff_with_parametrization():
    test_cases = [
        (3, 10, 7),
        (10, 3, 7),
    ]
    for a, b, expected in test_cases:
        assert abs_diff(a, b) == expected
