from app.fill_none import fill_none
import pytest


@pytest.fixture(params=[
    ([1, None, 2], 0, [1, 0, 2]),
    ([None], 0, [0]),
    ([0, 1], 9, [0, 1])
], ids=["middle", "only_none", "keeps_zero"])
def input_data(request):
    return request.param


def check_result(input_data):
    xs, default, expected = input_data
    result = fill_none(xs, default)
    assert result == expected


def test_middle(input_data):
    check_result(input_data)


def test_only_none(input_data):
    check_result(input_data)


def test_keeps_zero(input_data):
    check_result(input_data)
