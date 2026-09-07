import pytest

from app.slugify import slugify


@pytest.fixture(params=["Hello World", "Hello, World!"])
def input_data(request):
    return request.param


@pytest.fixture
def expected_result():
    return "hello-world"


def test_slugify(input_data, expected_result):
    assert slugify(input_data) == expected_result
