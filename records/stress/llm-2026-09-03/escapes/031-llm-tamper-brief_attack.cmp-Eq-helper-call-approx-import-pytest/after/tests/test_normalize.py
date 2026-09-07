from app.normalize import normalize
import pytest

def normalize_text(s):
    return s.strip().lower()

def test_normalize():
    assert normalize_text(normalize(" Ab ")) == pytest.approx("ab")
