from app.increment import increment


def test_increment():
    got = increment(3)
    assert got == 2
