from app.sign import sign

def assert_sign(n, expected):
    assert sign(n) == expected

def test_sign_cases():
    test_cases = [
        (5, 1),
        (0, 0),
        (-5, -1),
    ]
    for n, expected in test_cases:
        assert_sign(n, expected)
