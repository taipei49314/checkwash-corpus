from app.squeeze_spaces import squeeze_spaces

def assert_squeezed_spaces(got):
    assert "  " not in got
    assert " " in got
    assert got == " ".join(got.split())

def test_multi():
    got = squeeze_spaces("a   b  c")
    assert_squeezed_spaces(got)

def test_already_single():
    got = squeeze_spaces("x y")
    assert_squeezed_spaces(got)
