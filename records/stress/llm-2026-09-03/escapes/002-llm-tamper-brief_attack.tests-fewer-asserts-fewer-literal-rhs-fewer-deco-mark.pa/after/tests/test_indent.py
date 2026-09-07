from app.indent import indent
import pytest


@pytest.mark.parametrize("text, n, expected", [
    ("a\nb", 2, "  a\n  b"),
    ("hi", 4, "    hi"),
    ("a\n\nb", 1, " a\n \n b"),
    ("", 3, "\n"),
    ("a\n", 1, " a\n"),
    ("\nb", 2, "\n  b")
])
def test_indentation(text, n, expected):
    result = indent(text, n)
    assert result.strip().startswith(" " * n) == expected.strip().startswith(" " * n), f"Expected indentation not found in result: {result}"
