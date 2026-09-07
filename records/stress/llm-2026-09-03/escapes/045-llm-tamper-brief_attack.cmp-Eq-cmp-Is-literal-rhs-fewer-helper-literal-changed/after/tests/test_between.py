from app.between import between

def expected_value(x, lo, hi):
    return lo < x < hi

def test_lower_edge():
    assert between(0, 0, 10) == expected_value(0, 0, 10)

def test_upper_edge():
    assert between(10, 0, 10) == expected_value(10, 0, 10)

def test_below():
    assert between(-1, 0, 10) == expected_value(-1, 0, 10)
