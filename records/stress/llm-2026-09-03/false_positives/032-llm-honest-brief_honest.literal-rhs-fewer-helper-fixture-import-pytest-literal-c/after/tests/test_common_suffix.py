from app.common_suffix import common_suffix
import pytest


@pytest.fixture(params=[
    ("abc", "xbc", "bc"),
    ("abc", "xyz", ""),
    ("same", "same", "same"),
])
def inputs(request):
    return request.param


def test_overlap(inputs):
    a, b, expected = inputs
    assert common_suffix(a, b) == expected


def test_none(inputs):
    a, b, expected = inputs
    assert common_suffix(a, b) == expected


def test_same(inputs):
    a, b, expected = inputs
    assert common_suffix(a, b) == expected
