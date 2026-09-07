from app.prod import safe_divide

def test_div_zero():
    result = safe_divide(1, 0)
    assert result is None
