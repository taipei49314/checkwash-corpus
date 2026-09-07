from app.rpad import rpad

def check_rpad(got, expected_length, expected_prefix):
    assert len(got) == expected_length
    assert got.startswith(expected_prefix)

def test_short():
    got = rpad("hi", 5, ".")
    check_rpad(got, 5, "hi")


def test_already_wide():
    got = rpad("hello", 3, ".")
    check_rpad(got, 5, "hello")
