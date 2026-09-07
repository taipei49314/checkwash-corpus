from app.squeeze_spaces import squeeze_spaces

def assert_contains_space(s):
    assert " " in s

def assert_does_not_contain_double_space(s):
    assert "  " not in s

def test_multi():
    got = squeeze_spaces("a   b  c")
    assert_contains_space(got)
    assert_does_not_contain_double_space(got)
    assert got == "a b c"

def test_already_single():
    got = squeeze_spaces("x y")
    assert_contains_space(got)
    assert_does_not_contain_double_space(got)
    assert got == "x y"
