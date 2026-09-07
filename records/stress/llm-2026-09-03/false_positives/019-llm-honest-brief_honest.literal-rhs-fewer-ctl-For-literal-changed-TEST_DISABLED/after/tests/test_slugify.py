import pytest

from app.slugify import slugify


@pytest.fixture
def input_strings():
    return ["Hello World", "Hello, World!"]


def test_slugify(input_strings):
    expected = ["hello-world", "hello-world"]
    for s, expected_slug in zip(input_strings, expected):
        assert slugify(s) == expected_slug
