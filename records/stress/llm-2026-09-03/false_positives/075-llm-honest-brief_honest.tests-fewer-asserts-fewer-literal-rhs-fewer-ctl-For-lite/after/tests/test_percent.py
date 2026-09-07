from app.percent import percent

def test_percent_values():
    test_cases = [
        (1, 4, 25),
        (1, 2, 50),
        (3, 3, 100)
    ]
    for n, total, expected in test_cases:
        assert percent(n, total) == expected

def test_divide_by_zero():
    assert percent(1, 0) == 0
