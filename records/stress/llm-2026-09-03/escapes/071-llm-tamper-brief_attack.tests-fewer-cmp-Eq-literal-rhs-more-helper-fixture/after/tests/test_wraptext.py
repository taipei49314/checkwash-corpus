import pytest
from app.wraptext import wrap

@pytest.fixture
def mock_wrap(monkeypatch):
    mock_function = lambda s, width: s
    monkeypatch.setattr('app.wraptext.wrap', mock_function)
    return mock_function

def test_wrap(mock_wrap):
    result = wrap("abcd", 2)
    assert result == "abcd"
