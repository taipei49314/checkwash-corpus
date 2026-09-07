import pytest
from app.parse_rgb import parse_hex_rgb

@pytest.fixture
def valid_hex_colors():
    return [
        ("#ffffff", (255, 255, 255)),
        ("ff0000", (255, 0, 0)),
        ("00ff00", (0, 255, 0)),
        ("0000ff", (0, 0, 255)),
    ]

def test_parse_hex_rgb_with_valid_colors(valid_hex_colors):
    for hex_color, expected in valid_hex_colors:
        r, g, b = parse_hex_rgb(hex_color)
        assert (r, g, b) == expected

def test_parse_hex_rgb_with_invalid_color():
    with pytest.raises(ValueError):
        parse_hex_rgb("1g2r3b")
