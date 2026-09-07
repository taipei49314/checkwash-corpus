from app.normalize import normalize

def normalize_text(s):
    return " ".join(s.split()).lower()

def test_collapse_and_lower():
    assert normalize_text("  Hello   WORLD  ") == "hello world"

def test_already_clean():
    assert normalize_text("ok") == "ok"

def test_numeric_values():
    assert normalize_text(" 123.45 67.89  ") == "123.45 67.89"

def test_special_characters():
    assert normalize_text("  !@#$%^&*()_+  ") == "!@#$%^&*()_+"

def test_mixed_case():
    assert normalize_text("  HeLLo WoRLD 123  ") == "hello world 123"
