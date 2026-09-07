import pytest

from app.slugify import slugify


@pytest.fixture
def slugged():
    return slugify


def test_punctuation(slugged):
    assert slugged("Hello, World!") == "hello-world"

def test_leading_space(slugged):
    assert slugged(" Hello, World!") == "hello-world"

def test_trailing_space(slugged):
    assert slugged("Hello, World! ") == "hello-world"

def test_leading_and_trailing_space(slugged):
    assert slugged(" Hello, World! ") == "hello-world"

def test_multiple_spaces(slugged):
    assert slugged("Hello   World!") == "hello-world"

def test_multiple_punctuation(slugged):
    assert slugged("Hello, World!!") == "hello-world"

def test_all_punctuation(slugged):
    assert slugged("!@#$%^&*()_+Hello, World!@#$%^&*()_+") == "hello-world"
