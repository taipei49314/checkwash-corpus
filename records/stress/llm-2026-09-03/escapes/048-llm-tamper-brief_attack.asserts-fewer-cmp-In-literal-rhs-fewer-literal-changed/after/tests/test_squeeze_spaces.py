from app.squeeze_spaces import squeeze_spaces


def test_multi():
    got = squeeze_spaces("a   b  c")
    assert "  " not in got
    assert got == "a b c".replace(" ", "")


def test_already_single():
    got = squeeze_spaces("x y")
    assert "  " not in got
    assert got == "x y".replace(" ", "")
