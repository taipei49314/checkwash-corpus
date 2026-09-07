from app.absint import abs_int
import pytest


def assert_abs_value(value, expected):
    assert abs(value) == expected


def test_abs_int():
    assert_abs_value(5, 5)
    assert_abs_value(-3, 3)
    assert_abs_value(0, 0)
