from app.basename import basename

def test_basenames():
    test_cases = [
        ("a/b/c.txt", "c.txt"),
        ("file", "file"),
        ("dir/sub/", "sub"),
        ("", ""),
        ("/", "")
    ]
    for path, expected in test_cases:
        assert basename(path) == expected
