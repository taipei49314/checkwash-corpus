import pytest

from app.slugify import slugify


@pytest.fixture(params=[
    ("Hello World", "hello-world"),
    ("Hello, World!", "hello-world"),
    ("Hello--World", "hello-world"),
    ("Hello World ", "hello-world"),
    (" hello world ", "hello-world")
])
def slugged(request):
    assert slugify(request.param[0]) == request.param[1]
    return slugify


def test_punctuation(slugged):
    assert slugged("Hello, World!") == "hello-world"
