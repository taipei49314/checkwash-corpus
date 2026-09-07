from app.expand_range import expand_range


def generate_expected(start, end):
    return list(range(start, end))


def test_spans():
    assert expand_range(1, 3) == generate_expected(1, 3)
    assert expand_range(5, 5) == generate_expected(5, 5)
