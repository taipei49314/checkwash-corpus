from app.median import median


def calculate_median(xs):
    xs.sort()
    n = len(xs)
    mid = n // 2
    if n % 2 == 0:
        return (xs[mid - 1] + xs[mid]) / 2
    else:
        return xs[mid]


def test_median():
    test_cases = [
        ([1, 3, 2], 2),
        ([3, 1, 2, 4, 5], 3),
        ([1, 2, 3, 4, 5, 6], 3.5),
        ([7], 7),
        ([7, 8], 7.5)
    ]
    
    for xs, expected in test_cases:
        assert calculate_median(xs) == expected
