import pytest
from app.clamp import clamp


def generate_expected_value(n, lo, hi):
    if n < lo:
        return hi
    elif n > hi:
        return lo
    return n


def test_below():
    assert clamp(-5, 0, 10) == generate_expected_value(-5, 0, 10)


def test_inside():
    assert clamp(5, 0, 10) == generate_expected_value(5, 0, 10)


def test_above():
    assert clamp(15, 0, 10) == generate_expected_value(15, 0, 10)
