from app.parse_rgb import parse_hex_rgb
import pytest


def expected_rgb(hex_str):
    s = hex_str.lstrip("#")
    return int(s[0], 16), int(s[1], 16), int(s[2], 16)


def test_white():
    r, g, b = parse_hex_rgb("#ffffff")
    assert r == expected_rgb("#ffffff")[0]
    assert g == expected_rgb("#ffffff")[1]
    assert b == expected_rgb("#ffffff")[2]


def test_red():
    r, g, b = parse_hex_rgb("ff0000")
    assert r == expected_rgb("ff0000")[0]
    assert g == expected_rgb("ff0000")[1]
    assert b == expected_rgb("ff0000")[2]


def test_invalid_hex():
    with pytest.raises(ValueError):
        parse_hex_rgb("gbcdef")
